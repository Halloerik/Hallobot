# Hallobot

A bot which assigns roles on your discord server.

## Dependencies

This program uses [Poetry](https://python-poetry.org/) for dependency management. For starting this bot, install poetry and after that install the needed packages via:

```bash
poetry install
```

Now you can call python in your newly created virtual environment. Simply activate it with the following command:

```bash
poetry shell
```

## Running the Bot

```bash
python bot.py <discord_bot_token>
```

## Commands

```bash
$hello
```
Make the bot respond with "Hello!"
___
```bash
$version
```
Make the bot respond with its current version.
___
```bash
$listen
```
Tells the bot which channel to use for its role assignment message
___
```bash
$stop_listen
```
Tells the bot to stop listening for role assignment purposes
___
```bash
$add_role roleName rolePing emoji
```
Adds a new role to the role assignment message
- It will edit its message to contain "emoji -> roleName"
- It will add a reaction with the selected emoji for users to click
- Upon clicking the emoji reaction the user will get the role rolePing
- If clicked again the role will be removed from the user again
___
```bash
$remove_role roleName 
$remove_role rolePing 
$remove_role emoji
```
Removes the role with any of the matching parameters from the role assignment message
___
```bash
$listen_eula messageID rolePing emoji
```
Sets a message with the given messageID as EULA-Message by adding a reaction with the specified emoji. 
Clicking on that emoji will give the user the role specified by the rolePing

Useful for making people read the server rules before accessing other parts of the server
___
```bash
$stop_listen_eula
```
Removes the EULA function from the message set by $listen_eula
___
```bash
$list_roles
```
Prints out the message the bot listens to and the roles it listens for
___