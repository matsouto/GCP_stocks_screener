import os
import smtplib
import json
import functions_framework
import yfinance as yf
import pandas as pd
from tabulate import tabulate
from email.mime.text import MIMEText
from datetime import datetime, timedelta


def send_email(subject, body, sender, recipients, password) -> None:
    """
    Send an email using SMTP with SSL encryption.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        sender (str): The email address of the sender.
        recipients (list): A list of email addresses of the recipients.
        password (str): The password of the sender's email account.

    Returns:
        None

    Raises:
        Any exceptions raised by smtplib.SMTP_SSL, such as smtplib.SMTPAuthenticationError.

    Note:
        This function sends an email using the provided subject, body, sender, recipients, and password.
        It uses SMTP with SSL encryption to connect to the SMTP server at smtp.gmail.com on port 465.
        The email is sent in MIMEText format.

    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipients
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients.split(","), msg.as_string())
        print("Email sent!")
    except Exception as e:
        raise e


def ifr2_screener(oversold=25) -> str:
    """
    Calculate the IFR2 screener based on oversold condition.

    Args:
        oversold (int, optional): The oversold condition for the Relative Strength Index (RSI). Defaults to 25.

    Returns:
        None

    Note:
        This function calculates the IFR2 screener based on the oversold condition provided. It reads backtesting results from a CSV file, calculates the "Greatness Factor" based on the "Gain Factor" and "Profitable %" columns, downloads stock data using yfinance, calculates the RSI using the Wilder method, and filters stocks based on the oversold RSI condition. The final results are displayed in an ASCII table format.

    """
    period = 2
    timeframe = "1d"

    backtesting_result = pd.read_csv("./data/ifr2_best_stocks_backtesting.csv")

    backtesting_result["Greatness Factor"] = (
        backtesting_result["Gain Factor"] * backtesting_result["Profitable %"]
    )
    backtesting_result.sort_values(by="Greatness Factor", inplace=True)
    backtesting_result.reset_index(inplace=True)

    today = datetime.today()
    i_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    f_date = today.strftime("%Y-%m-%d")
    selected_stocks = [ticker + ".SA" for ticker in backtesting_result["Ticker"]]

    # Download data using yfinance
    data = yf.download(selected_stocks, start=i_date, end=f_date, interval=timeframe)

    close = data["Adj Close"].iloc[-1]
    var = (
        (data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2] * 100
    )

    # Wilder method for RSI
    # This calculation was made to match TradingView's RSI
    def calculate_rsi(data, window):
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    rsi = calculate_rsi(data["Close"], period).iloc[-1]

    df = pd.DataFrame(
        {
            "Close": close,
            "Var": var,
            "RSI": rsi,
        }
    ).reset_index(drop=False)

    df["Ticker"] = df["Ticker"].str.replace(".SA", "")  # Remove ".SA" suffix

    # Filtering based on oversold condition
    oversold_df = df[df["RSI"] <= oversold]
    # Merging to get the previous calculated columns
    oversold_df = oversold_df.merge(backtesting_result, how="left", on="Ticker")
    oversold_df.sort_values(by="Greatness Factor", ascending=False, inplace=True)
    oversold_df.reset_index(inplace=True, drop=True)

    ascii_table = tabulate(
        oversold_df[["Ticker", "Var", "RSI", "Greatness Factor"]],
        headers="keys",
        tablefmt="markdown",
    )

    return ascii_table


def get_env_vars(name="CREDENTIALS"):
    return os.environ.get(name, None)


@functions_framework.http
def screener_run(request) -> str:
    """
    HTTP Cloud Function.

    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    Note:
        For more information on how Flask integrates with Cloud
        Functions, see the `Writing HTTP functions` page.
        <https://cloud.google.com/functions/docs/writing/http#http_frameworks>
    """

    subject = "IFR2 Screener - Daily Collection"
    body = ifr2_screener()

    credentials = get_env_vars()

    if credentials == None:
        raise Exception("Coudn't get credentials.")

    try:
        credentials_json = json.loads(credentials)
    except json.JSONDecodeError:
        raise ValueError("Environment variable is not a valid JSON string.")

    sender = credentials_json["sender"]
    recipients = credentials_json["recipients"]
    password = credentials_json["password"]

    send_email(subject, body, sender, recipients, password)
    return body
