## Cost Tracker App

## Software Used
Python Flask
Jinja2 
PostgreSQL

## Tools Used
Visual Studio (VScode)

## External API 
[Venmo SDK](https://github.com/mmohades/Venmo)


## How To Run This App
Download from git hub
Run seed file
set venv from reqirements.txt
run flask on the terminal to start server
Set the admin user's role to 'admin' from psql terminal (refer to commented script on seed.py)
For payment and transactions set the access token through admin page
Get the access token using venmo username and password( refer to commented script on seed.py)

## TODO
Make users subcribe to groups
Only messages subscribed to the groups can be viewed(right now users can see all messages)
Make one person in the group as group owner to handle transactions, right now only admin is handling that
Have different algorithms for computing the expenses