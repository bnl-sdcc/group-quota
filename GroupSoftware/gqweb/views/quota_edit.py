# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from collections import defaultdict
from .. import app

from flask import request, render_template, redirect, url_for, flash
from ..db import db_session
from ..db.models import Group, build_group_tree_db, build_group_tree_formdata
from ..validation import validate_form_types, set_quota_sums


def set_params(db, formdata):
    """ Populate database objects in @db with user-input from @formdata """

    for name, params in formdata.iteritems():
        dbobj = next(x for x in db if x.group_name == name)
        for param, val in params.iteritems():
            if param == 'group_name' or param == 'new_name':
                continue
            if (isinstance(val, float) and abs(val - float(getattr(dbobj, param))) > 0.1) \
               or not isinstance(val, float):
                setattr(dbobj, param, val)

        # NOTE: Since form value isn't present if not checked!
        dbobj.accept_surplus = 'accept_surplus' in params


def set_renames(db, formdata):
    """ Detect renamed groups and fix them in the DB accordingly """

    def gen_tree_list(form):
        treelist = list(build_group_tree_formdata(formdata))
        return sorted(treelist, key=lambda x: x.full_name)

    root = gen_tree_list(formdata)
    existing_names = set(x.full_name for x in root)
    clean_root = gen_tree_list(formdata)

    # NOTE: Two copies needed for this traversal because we modify the first
    #       copy as we go in alphabetical order to allow renames to propogate
    #       correctly.
    for group, orig_grp in zip(root, clean_root):
        params = formdata[orig_grp.full_name]

        # Detect lowest-level changes in group name
        old = orig_grp.full_name.split('.')[-1]
        new = params.get('new_name', old)
        if old != new:
            # This will propogate through the tree if the group has children
            group.rename(new)

            if group.full_name in existing_names:
                raise ValueError("Multiple groups named %s found!" % group.full_name)

        # Find db-object that matches old name and rename it to match the
        # possibly modified group-tree
        obj = next(x for x in db if x.group_name == orig_grp.full_name)
        if obj.group_name != group.full_name:
            app.logger.info("Group rename detected!: %s->%s",
                            obj.group_name, group.full_name)
            obj.group_name = group.full_name

    app.logger.info("\n".join(map(str, root)))


@app.route('/edit', methods=['POST'])
def edit_groups_form():
    data = defaultdict(dict)
    for k, value in request.form.iteritems():
        group, parameter = k.split('+')
        data[group][parameter] = value

    errors = list()
    for grpname in data:
        data[grpname], e = validate_form_types(data[grpname])
        errors.extend(e)

    if errors:
        return render_template('edit_group.html', errors=errors)

    db_groups = Group.query.all()

    set_params(db_groups, data)

    root = build_group_tree_db(db_groups)

    try:
        set_quota_sums(db_groups, root)
        set_renames(db_groups, data)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('edit_groups_form'))
    else:
        # Objects in session.dirty are not necessarily modified if the set-attribute
        # is not different than the current one
        if any(x for x in db_session.dirty if db_session.is_modified(x)):
            flash("Everything OK, changes committed!")
        else:
            flash("No changes were made!", "nochange")

        db_session.commit()

    return redirect(url_for('main_menu'))