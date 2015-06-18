# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from collections import defaultdict
from . import app

from flask import request, render_template, redirect, url_for, flash
from database import db_session
from models import Group, build_group_tree_db, type_map, build_group_tree_formdata


def validate_form_types(data):
    errors = list()
    for k, v in data.items():
        if k == 'group_name':
            continue
        fn, valid, msg = type_map[k]
        try:
            data[k] = fn(v)
            if not valid(data[k]):
                raise ValueError
        except ValueError:
            errors.append((data['group_name'], k, msg))

    return data, errors


def set_params(db, formdata):
    for name, params in formdata.iteritems():
        dbobj = next(x for x in db if x.group_name == name)
        for param, val in params.iteritems():
            if param == 'group_name' or param == 'new_name':
                continue
            setattr(dbobj, param, val)

        # NOTE: Since form value isn't present if not checked!
        dbobj.accept_surplus = 'accept_surplus' in params


def set_quota_sums(db, root):
    for group in root:
        if not group.is_leaf:
            newquota = sum(x.quota for x in group.get_children())

            # FIXME: and not user_sum_change_auth
            if newquota != group.quota and True:
                app.logger.info("Intermediate group sum %s: %d->%d",
                                group.full_name, group.quota, newquota)
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.quota = newquota
                group.quota = newquota


def set_renames(db, formdata):

    def gen_tree_list(form):
        treelist = list(build_group_tree_formdata(formdata))
        return sorted(treelist, key=lambda x: x.full_name)

    root = gen_tree_list(formdata)
    clean_root = gen_tree_list(formdata)

    for group, orig_grp in zip(root, clean_root):
        params = formdata[orig_grp.full_name]

        old = orig_grp.full_name.split('.')[-1]
        new = params.get('new_name', old)
        # app.logger.debug("Old->New: %s->%s", old, new)
        if old != new:
            group.rename(new)
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

    set_quota_sums(db_groups, root)

    set_renames(db_groups, data)

    # Objects in session.dirty are not necessarily modified if the set-attribute
    # is not different than the current one
    if any(x for x in db_session.dirty if db_session.is_modified(x)):
        flash("Everything OK, changes committed!")
    else:
        flash("No changes were made!", "nochange")

    db_session.commit()

    return redirect(url_for('main_menu'))
