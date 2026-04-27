import sys
sys.path.insert(0, '.')
from src.db_helper import get_record_by_id, load_all, get_paged_data_sql

# Get all projects
all_projects = load_all()
print('All projects:', all_projects)

# Get specific project by ID
project = get_record_by_id(1)
print('Project 1:', project)

# Get paged data
page_data = get_paged_data_sql(1, 50, 'Tracking ID', 'desc')
print('Paged data:', page_data)
