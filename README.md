# notion-game-tracker-autocomplete
Autocomplete integration for Notion game tracker 


## Usage
| Argument                | Description                                                                                                                         | Default |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------|---------|
| `-h`, `--help`          | Show help                                                                                                                           | `False`   |
| `-l`, `--list-all`          | Choose between all posibble matches                                                                                                 | `False`   |
| `-r`, `--replace`           | Replace existing data for found fields                                                                                           | `False`   |
| `-s`, `--show-untouched`    | Also print message for entries that are not going to be updated                                                                     | `True`    |
| `-v`, `--verbose`           | Show updated values                                                                                                                 | `False`   |
| `-m MODE`, `--mode MODE`    | `watch`: look for new entries to update in database ending in '#'<br/> `one`: update database entry with title `[--title]`<br/> `all`: update all | `watch` |
| `-t TITLE`, `--title TITLE` | Title to find when using `mode=one`                                                                                                   | `""`      |

## Set up
1. Install dependencies
    ```bash
    # if pip not installed
    sudo apt install python3-pip

    pip install -r requirements.txt
    ```
2. Add a new connection to the template and enable it.
3. Get you IGDB credentials.
4. Edit the file `.env` with your data:
    ```bash
    IGDB_ID="<YOUR_IGDB_ID>"
    IGDB_TOKEN="<YOUR_IGDB_TOKEN>"
    NOTION_DATABASE_ID="<YOUR_NOTION_DATABASE_ID>"
    NOTION_TOKEN="<YOUR_NOTION_TOKEN (starts with secret)>"
    ```

## [Template](https://living-spy-6cc.notion.site/Game-Tracker-Template-c18219f911ea41c7974accdf2ee58fb1?pvs=4)
![](./img/dashboard.PNG)

![](./img/dashboard2.PNG)

<img src="./img/dashboard3.PNG" alt="drawing" width="600"/>



### Example
```bash
python3 gametracker.py -m watch
```
![example](./img/gametracker.gif)