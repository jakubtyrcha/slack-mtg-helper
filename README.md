# slack-mtg-helper

A slack tournament-management app using AWS DynamoDB and deployable to AWS Lambda using Zappy.

Use command 'mtg-util' to create 'control panel' message and add a tournament. Each tournament is in its own slack thread and can be managed via buttons in the top message. All duels are appended to the thread and can be deleted if needed. 'Current status' button sends a private message with missing duels and current 'table'.

calc.py has some deck probability formulas 

Known issues:
* sometimes the AWS lambda takes too long and timeout is reached
