## hamradiologger
`hamradiologger` is meant to be a fast, responsive logging program which runs from the command line and leverages the [QRZ.com API](https://www.qrz.com/docs/logbook30/api) to:

*   Query QRZ.com for data on specific callsigns
*   Query your log for contact history with a specific callsign
*   Write QSO's to your QRZ.com log

To use this program successfully, *__you will need to be a paid QRZ.com subscriber (XML level or higher) and have an API key__*.

### Installation

You can either download the `logger.py ` and `qrz.py` into a directory of your choosing, or simply run:

```
git clone https://github.com/mkershis/hamradiologger
```
You would then `cd` into this directory and run:
```
python logger.py
```
Alternatively, I'd recommend creating a `bash` alias or `PowerShell` function so that you can run the program from anywhere.

### Initial Setup

Once you have the files downloaded and aliases created (if desired), you're ready to run the program assuming you have the necessary dependencies installed as well (see below). The program is designed to pull your QRZ.com username, password, and API key from appropriately set environment variables. If the variables aren't set, the program is going to prompt you for each of these every time to run the logger, so I'd recommend configuring these for yourself. The variable names are as follows:
```
QRZ_USERNAME
QRZ_PASSWORD
QRZ_API_KEY
```
Note that while this method is secure in the sense that it doesn't require you to store your passwords in a file, it means that running the logging program will be specific to your log. This makes it difficult if you want to let someone else log on your computer. Fortunately it is possible to override this behavior by starting the logger with the following option:
```
python logger.py -p True
```
The `-p True` argument will set the program to prompt the user for credentials regardless, thus ignoring the environment variables and allowing another operator to log on your PC and write to *__their__* log instead.

### Basic Usage
The intended use for this program is for quickly logging multple contacts over a single session by minimizing the amount of input required from the user. Here it's assumed that the user will be working a particular band and mode for the duration of the session, so if you wish to change bands or modes, it's best to restart the logger. The tradeoff here is that you just have to specify the band and mode at the beginning of the session rather than specifying it for each contact. Example usage:
```
Enter the band you are using (e.g. 10m, 40m): 10m
Enter the mode you are using (e.g. FT8, SSB): ssb
```
You don't have to worry about upper/lower case as the program will normalize your inputs to upper case. This was done to maximize efficiency in looking up callsigns.

*Note: If you just want to use the logger to lookup callsigns, you can leave these options blank as nothing will be written to your log unless you are explicitly logging a contact*

A typical callsign lookup might be as follows:

```
Enter the callsign you wish to search for ("q" to quit): W1AW  # hit enter...
Details for W1AW:

Aliases

ARRL HQ OPERATORS CLUB
225 MAIN ST
NEWINGTON, CT 06111
United States

QSL Info: US STATIONS PLEASE QSL VIA LOTW OR DIRECT WITH SASE.

QSL Preferences
LOTW?: Yes
eQSL?: No
Mail?: Yes

You are working W1AW for the first time!

Do you wish to start a concat with W1AW (y/n)?:
```
This screen shows some basic data for the operator you searched for including address and their QSL preferences. If you haven't worked the person before then the program tells you that you're working them for the first time. If you choose to log the contact, the program will automatically make note of the contact start time (in UTC) the second you hit Enter. Then you'll be prompted to enter the signal report data:
```
Enter the signal report you sent to the other station (e.g. 59): 57
Enter the signal report you received from the other station: 55
Hit enter to end the QSO
```
At this point the program will wait for you to hit enter again to end the QSO and automatically record the end time for the QSO. This is done so that if you are ragchewing for a while, you can get an accurate end time for the QSO. 

Of course, the signal reports are optional and you can leave these blank.

Now let's say we'd previously worked W1AW on Saturday January 25, 2024 at 1530 UTC on 20M FT8. Then instead of seeing "You are working W1AW for the first time!" we'd see:

```
You worked W1AW 1 time(s) on the following date(s):

    Sat Jan 25, 2024 between 1530-1530 UTC on 20M FT8
```
While it's generally interesting to know if you've worked a particular contact previously, this is also helpful to avoid logging duplicate contacts on the same session (for example). The logging process (to your QRZ.com log) is instantaneous, so if you logged a contact and searched for that callsign immediately afterward, you should see the results here.

Once you're finished logging contacts, just type "q" at the next callsign search prompt to end the program. The program will then report back the number of searches you performed, the number of contacts logged, and the total run time for the program:
```
You looked up 3 callsign(s) and logged 1 contact(s) in a total runtime of 00:10:09 (h:m:s)
```
### Dependencies
Much of this program uses the Python standard library, but there are some dependencies to be aware of:
#### Required
* `bs4` - Since interfacing the QRZ log involves parsing XML, you will need to have `BeautifulSoup` installed (try ```pip install beautifulsoup4```). hamradiologger was developed using ver. `4.12.3`
#### Optional
*   `pandas` - There is a `queryAll()` function in the `qrz` library which effectively downloads all of the entries in your QRZ.com log and returns the data in a pandas dataframe. While this function isn't needed to run the logger or lookup functions, you will need pandas if you wish to use it separately. I used version `2.2.2`.