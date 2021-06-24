#!/usr/bin/env python3
"""asana2csv.py
Modificated script by https://tech.surveypoint.com/posts/export-all-your-asana-tasks/

Export all tasks from my Asana workspace to CSV
Requires asana library.  See https://github.com/Asana/python-asana
Requires workspace as parameter.
"""

import sys
import csv
import datetime
import asana
import os

# NOTE: API keys are deprecated, may no longer work.
# See: https://asana.com/developers/documentation/getting-started/auth#personal-access-token
# Generate access token in Asana: My Profile Settings | Apps | Manage Developer Apps

MY_PERSONAL_ACCESS_TOKEN = 'YOUR_KEY'
OUT_FILE_PATH = "YOUR_PATH_EXAMPLE C:/Users/User1/PycharmProjects/UnloadAsanaCSV/downloads"
OUT_FILE_NAME_ROOT = 'asana_tasks'
CSV_OUT_HEADER = ['proj_name', 'ms_name', 'task_title', 'completed_on', 'priority']
REC_LIMIT = 99999
# New Asana API requires pagination for large collections, specify item_limit to be safe
ITEM_LIMIT = 100
PAGE_SIZE = 50

CSV_OUT_HEADER = ['Task', 'Project', 'Workspace', 'DueDate', 'CreatedAt', \
    'ModifiedAt', 'Completed', 'CompletedAt', 'Assignee', 'AssigneeStatus', \
    'Parent', 'Notes', 'Taskgid']

def write_csv_records(csv_out_file_name, csv_header_list, csv_record_list):
    """Write out selected columns into CSV file."""
    with open(csv_out_file_name, 'w', encoding='utf8') as csv_file:
        csvwriter = csv.writer(csv_file, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(csv_header_list)
        for item in csv_record_list:
            csvwriter.writerow(item)
    return

def get_workspace_dict(workspaces):
    """Return a dictionary with gid and name of each workspace."""
    this_dict = {}
    for workspace in workspaces:
        this_dict[workspace['gid']] = workspace['name']
    return this_dict

def process_project_tasks(client, project, ws_dict):
    """Add each task for the current project to the records list."""
    task_list = []
    while True:
        tasks = client.tasks.find_by_project(project['gid'], {"opt_fields":"name, \
            projects, workspace, gid, due_on, created_at, modified_at, completed, \
            completed_at, assignee, assignee_status, parent, notes"})
        for task in tasks:
            ws_name = ws_dict[task['workspace']['gid']]
            # Truncate most of long notes -- I don't need the details
            if len(task['notes']) > 80:
                task['notes'] = task['notes'][:79]
            assignee = task['assignee']['gid'] if task['assignee'] is not None else ''
            created_at = task['created_at'][0:10] + ' ' + task['created_at'][11:16] if \
                    task['created_at'] is not None else None
            modified_at = task['modified_at'][0:10] + ' ' + task['modified_at'][11:16] if \
                    task['modified_at'] is not None else None
            completed_at = task['completed_at'][0:10] + ' ' + task['completed_at'][11:16] if \
                task['completed_at'] is not None else None
            rec = [task['name'], project['name'], ws_name, task['due_on'], created_at, \
                modified_at, task['completed'], completed_at, assignee, \
                task['assignee_status'], task['parent'], task['notes'], task['gid']]
            rec = ['' if s is None else s for s in rec]
            task_list.append(rec)
        if 'next_page' not in tasks:
            break
    return task_list

def main():
    """Main program loop."""
    def usage():
        """Show usage if user does not supply parameters."""
        text = """
usage: asana2csv.py <WORKSPACE_NAME>
"""

        print(text)

    # Check command line parameters; require name of workspace
    if (len(sys.argv) < 2) or (len(sys.argv) > 2):
        usage()
        sys.exit(0)
    my_workspace = sys.argv[1]

    now_day = str(datetime.date.today())
    my_filename = '_'.join([OUT_FILE_NAME_ROOT, my_workspace, now_day + '.csv'])
    csv_out_file = os.path.join(OUT_FILE_PATH, my_filename) #'/'.join([OUT_FILE_PATH, my_filename])


    # Old API used keys and basic auth; new API uses Oauth2 or tokens
    #asana_api = asana.asanaAPI(MY_API_KEY, debug=True)
    #client = asana.Client.basic_auth(MY_API_KEY)
    client = asana.Client.access_token(MY_PERSONAL_ACCESS_TOKEN)
    client.options['page_size'] = 100
    my_client = client.users.me()

    # Build dictionary of workspace names associated with each workspace gid.
    # This isn't strictly needed for querying a single workspace.
    ws_dict = get_workspace_dict(my_client['workspaces'])

    # Find the requested workspace; iterate through all projects and tasks
    this_workspace = next(workspace for workspace in my_client['workspaces'] if \
        workspace['name'] == my_workspace)
    all_projects = client.projects.find_by_workspace(this_workspace['gid'], iterator_type=None)

    db_list = []
    for project in all_projects:
        print(project['name'])
        db_list.extend(process_project_tasks(client, project, ws_dict))

    write_csv_records(csv_out_file, CSV_OUT_HEADER, db_list)

    return

if __name__ == '__main__':
    main()