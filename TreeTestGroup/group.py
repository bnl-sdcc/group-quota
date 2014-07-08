#!/usr/bin/python

# *****************************************************************************
# Group class used for Group creation, and eventual tree creation.
#
# Uses the atlas_group_quotas MySQL table to initialize the groups and 
# dynamically populate the tree structure. When used with test.py, analyzes 
# current and previous group queue amounts to determine accept_surplus flags.
# *****************************************************************************
#
# Includes script to query the MySQL database for the group_names and populate
# the necessary fields accordingly. The tree is created using the current '.'
# divider to separate parent from child in the group_name field. 
# Those without a '.', are children of the root node.
#
# 1. Query MySQL database and populate the group_list
# 2. Sort the list and begin with the first entry
# 3. Populate the tree with a backtrack algorithm
# 4. Added a function to traverse the tree and update the data table's surplus 
#    values based upon the surplus check analysis
#
# Added Group Functions:
#		tree_creation(self, cur, con):  creates the tree, for analysis
#		enable_surplus_changes(self, cur, con): updates the data table
#		(Helper methods) -- aquire_groups, get_surplus, set_surplus
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 6/13/14 *updated 7/8/14
#
# *****************************************************************************
import sys
import MySQLdb
import logging

############################ VARIABLES ############################
# List of group names to eventually populate from Database
group_list = []

# Database parameters
dbtable = 'atlas_group_quotas'
dbhost = 'old-db.rcf.bnl.gov'
database = 'atlas_demand'
dbuser = 'group_edit'
dbpass = 'atlas'

# Table Fields for ease of future modification in case they are changed
group_name = 'group_name'
quota = 'quota'
priority = 'priority'
accept_surplus = 'accept_surplus'
busy = 'busy'
threshold = 'surplus_threshold'
last_update = 'last_update'

# MySQL variable getter
get_Mysql_Val = 'SELECT %s FROM %s WHERE %s="%s"'
get_Mysql_groups = 'SELECT %s FROM %s;'
set_Mysql_surplus = 'UPDATE %s SET %s=%d WHERE %s="%s";'

########################## HELPER METHODS ##########################

# Populates the group_list with the groups in the database
def aquire_groups(cur, con):
  cur = con.cursor()
  cur.execute(get_Mysql_groups % (group_name, dbtable))
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    group_list.append(x)
  

def get_surplus(name, cur):
  cur.execute(get_Mysql_Val % (accept_surplus, dbtable, group_name, name))
  value = cur.fetchone()[0]
  return value


def set_surplus(name, value, cur, con):
  check = get_surplus(name, cur)
  if check != value:
    log.info("###########################################################################")
    log.info("######### Changing surplus of %s from %d to %d #########", name, check, value)
    log.info("###########################################################################")
    cur.execute(set_Mysql_surplus % (dbtable, accept_surplus, value, group_name, name))
    con.commit()

###################################################################

# Group Object for group creation and tree formulation
class Group(object): 
  def __init__(self, name):
    
    self.name = name
    self.quota = None
    self.priority = None
    self.accept_surplus = None
    self.threshold = None
    
    #### FOR TREE ####
    self.parent = None
    self.children = {}
    ###################	  
    
    if name != '<root>': # IF ROOT, NO VALUES
      try:
	con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass, db=database)
      except MySQLdb.Error as E:
	log.error("Error connecting to database: %s" % E)
	return None
      
      cur = con.cursor()
      # OBTAIN QUOTA
      cur.execute(get_Mysql_Val % (quota, dbtable, group_name, name))
      self.quota = cur.fetchone()[0]
      # OBTAIN Priority
      cur.execute(get_Mysql_Val % (priority, dbtable, group_name, name))
      self.priority = cur.fetchone()[0]
      # OBTAIN ACCEPT_SURPLUS
      cur.execute(get_Mysql_Val % (accept_surplus, dbtable, group_name, name))
      self.accept_surplus = cur.fetchone()[0]
      # OBTAIN THRESHOLD
      cur.execute(get_Mysql_Val % (threshold, dbtable, group_name, name))
      self.threshold = cur.fetchone()[0]
      
      cur.close()
      con.close()	
	
  def add_child(self, name):
	  # Add a child node to this one, setting it's parent pointer
	  child = Group(name)
	  child.parent = self
	  self.children[name] = child
	  return child # Return child node for tree creation node pointer
  
  # Recursively iterate through all lower nodes in the tree
  def walk(self):
	  if not self.children:
	      return
	  for x in self.children.values():
	      yield x
	      for y in x.walk():
		  yield y
		  
  # Return group by name
  def get_by_name(self, name):
	  if self.name == name:
	      return self
	  for x in self.walk():
	      if name == x.name:
		  return x
	  raise Exception("No group %s found" % name)
  
  #def get_sibling_surplus(self, priority_value)
    
  # Check if parent has surplus flag, for future use  
  def check_parent_surplus(self):
	if self.parent.accept_surplus == 1:
	  return True
	else:
	  return False
    
  def __iter__(self):
	  return iter(self.walk())
      
  def __str__(self):
	  if self.name != '<root>': # Root has no values in table
	    return '%s: quota: %d, priority: %d, surplus: %s, threshold: %d' % \
		  (self.name, self.quota, self.priority, self.accept_surplus, self.threshold)
	  else:
	    return '%s' % \
		  (self.name)
		
  # Creates Group tree, Returns root node. Generated generically based on "." placement
  def tree_creation(self, cur, con):
    aquire_groups(cur, con)		# Populate group_list
    group_list.sort()		# Sort list
    current_node = self		# Set node to use as pointer to root
    prefix = None		# prefix  for parent/child identification
    for x in group_list:
      if '.' not in x: 		# No '.' denotes tier 1 group
	current_node = self	# Set current current_node to root current_node
	current_node = current_node.add_child(x)	# add child and adjust pointer
	prefix = x		# Set new prefix
      elif x.startswith(prefix):
	prefix = x		# Update prefix
	current_node = current_node.add_child(prefix) # add and adjust	
      else:
	# Used to backtrack if prefix not recognized
	while not x.startswith(prefix) & (prefix != '<root>'):
	  current_node = current_node.parent 	# Backtrack
	  prefix = current_node.name 		# Update prefix
	current_node = current_node.add_child(x)	# add and adjust
	prefix = x				# Update prefix
    return self
  
  # Traverse the constructed group tree and update the accept_surplus values in the table, if necessary 
  def enable_surplus_changes(self, cur, con):
    def child_walk(node):
      if node is not None:
	if not node.children and node.priority > 0:
	  set_surplus(node.name, node.accept_surplus, cur, con)
	for n in node.children.values():
	  child_walk(n)
    child_walk(self)