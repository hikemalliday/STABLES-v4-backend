# STABLES-v4-backend
#### Backend server for [STABLES-v4-frontend](https://github.com/hikemalliday/STABLES-v4-frontend)]

The FastAPI backend is connected to a local MSSQL server on my machine.
The backend searches the Everquest directory for log files (these log files are named similar to the characters). The log files are the read, formatted, and inserted into the SQL server.
Tables:

-dbo.users: Stores usernames and passwords. The passwords are hashed.

-dbo.characters: Stores the info about a character

-dbo.inventory: Stores the info for a given characters inventory

-dbo.spellbooks: Stores the info for a given characters spellbook

-dbo.eqDir: Stores the everquest directory path (string)

