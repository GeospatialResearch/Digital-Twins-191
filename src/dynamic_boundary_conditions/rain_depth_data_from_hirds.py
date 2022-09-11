# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 14:35:08 2022.

@author: pkh35
"""

import requests
from requests.structures import CaseInsensitiveDict
import re
import pandas as pd
import pathlib


def get_site_url_key(site_id: str) -> str:
    """Get each sites' unique url key from the hirds website using curl commands"""
    url = "https://api.niwa.co.nz/hirds/report"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json, text/plain, */*"
    headers["Accept-Language"] = "en-GB,en-US;q=0.9,en;q=0.8"
    headers["Connection"] = "keep-alive"
    headers["Content-Type"] = "application/json"
    headers["Origin"] = "https://hirds.niwa.co.nz"
    headers["Referer"] = "https://hirds.niwa.co.nz/"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "same-site"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
        Chrome/96.0.4664.110 Safari/537.36"
    headers["sec-ch-ua"] = '"" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96""'
    headers["sec-ch-ua-mobile"] = "?0"
    headers["sec-ch-ua-platform"] = '""Windows""'
    # Set idf to false for rainfall depth data, and set idf to true for rainfall intensity data.
    data = f'{{"site_id":"{site_id}","idf":false}}'
    resp = requests.post(url, headers=headers, data=data)
    rainfall_results = pd.read_json(resp.text)
    # Get requested sites url unique key
    site_url = rainfall_results["url"][0]
    pattern = re.compile(r"(?<=/asset/)\w*(?=/)")
    site_url_key = re.findall(pattern, site_url)[0]
    return site_url_key


def get_data_from_hirds(site_id: str) -> str:
    """Get data from the hirds website using curl command and store as a csv files."""
    site_url_key = get_site_url_key(site_id)
    url = rf"https://api.niwa.co.nz/hirds/report/{site_url_key}/export"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json, text/plain, */*"
    headers["Accept-Language"] = "en-GB,en-US;q=0.9,en;q=0.8"
    headers["Connection"] = "keep-alive"
    headers["Origin"] = "https://hirds.niwa.co.nz"
    headers["Referer"] = "https://hirds.niwa.co.nz/"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "same-site"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
        Chrome/96.0.4664.110 Safari/537.36"
    headers["sec-ch-ua"] = '"" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96""'
    headers["sec-ch-ua-mobile"] = "?0"
    headers["sec-ch-ua-platform"] = '""Windows""'
    resp = requests.get(url, headers=headers)
    site_data = resp.text
    return site_data


def store_data_to_csv(site_id: str, file_path_to_store):
    """Store the depth data in the form of csv file in the desired path."""
    if not pathlib.Path.exists(file_path_to_store):
        file_path_to_store.mkdir(parents=True, exist_ok=True)

    filename = pathlib.Path(f"{site_id}_rain_depth.csv")
    site_data = get_data_from_hirds(site_id)
    with open(file_path_to_store / filename, "w") as file:
        file.write(site_data)
