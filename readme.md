# Shopping Analyzer

A Python tool to automatically extract and analyse your Lidl Plus receipts from `lidl.co.uk` using the official receipts API.

---

> **📹 YouTube Video Note**
>
> If you came here from a YouTube video, the setup has **changed**. The project now uses the **Lidl API** instead of web scraping, which is faster and more reliable.
>
> **Use this README as the source of truth** – not the video instructions.

---

## Overview

- **Automatic receipt import** from your Lidl Plus account (digital receipts only)
- **Smart updates**: only new receipts are fetched; existing ones are left untouched
- **Structured JSON output** in `lidl_receipts.json`
- **Interactive Streamlit dashboard** to explore spending, discounts and Lidl Plus savings
- Works primarily with **Lidl UK (`lidl.co.uk`)**, with the country logic now configurable in code

⚠️ **Data availability**: Lidl only exposes digital receipts from roughly **February 2023** onwards. Older receipts will not appear via the API.

---

## Prerequisites

- **Python 3.8+** (`python --version` to check)
- One of:
  - **Firefox** or **Chrome / Chromium** (for automatic cookie extraction), or
  - A way to export cookies to a JSON file
- An active **Lidl Plus** account with digital receipts visible on `https://www.lidl.co.uk/mla/`

---

## Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url>
   cd shopping-analyzer
   ```

   Or download the ZIP from GitHub and extract it.

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - macOS / Linux:

     ```bash
     source venv/bin/activate
     ```

   - Windows (PowerShell / CMD):

     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Authentication (cookies)

This tool uses your **existing Lidl Plus login session** by reusing your browser cookies or a cookie file. It does **not** know your password.

> **Security notice**
>
> - Cookie data can be as sensitive as a password.
> - **Never commit** `lidl_cookies.json` to Git or upload it anywhere.
> - Delete cookie files when you are done if you don’t need them.

You can authenticate in two ways:

### Option A – Automatic browser cookie extraction (recommended)

1. Open Firefox, Chrome or Chromium.
2. Log in to Lidl Plus at `https://www.lidl.co.uk/mla/` and keep the tab open.
3. Run the tool (see “Running the extractor” below) and choose the browser when prompted, or pass `--browser firefox|chrome|chromium` on the command line.

> On macOS, Chrome may fail due to keychain access restrictions. If you see a “key for cookie decryption” style error, use Firefox instead.

### Option B – Cookie file (`lidl_cookies.json`)

1. Use a browser extension such as **EditThisCookie** or **Cookie-Editor** to export cookies while logged in to Lidl Plus.
2. Save them as JSON to `lidl_cookies.json` in the project root (or another path you’ll pass via `--cookies-file`).

The file should contain an **array of cookie objects** (standard browser export JSON).

---

## Running the extractor

The main entry point is `get_data.py`. You can run it in **interactive** mode or with **explicit commands**.

### Interactive menu (simplest)

```bash
python get_data.py
```

You’ll get a menu:

1. **Initial Setup** – fetch all available digital receipts (first run)
2. **Update** – fetch only new receipts not already in `lidl_receipts.json`
3. **Exit**

The script will then ask how to authenticate:

- Firefox (automatic cookie extraction)
- Chrome
- Chromium
- Cookie file (`lidl_cookies.json`)

### Non-interactive examples

Initial import using Firefox cookies:

```bash
python get_data.py initial --browser firefox
```

Update using Chromium cookies:

```bash
python get_data.py update --browser chromium
```

Initial import using a cookie file:

```bash
python get_data.py initial --cookies-file lidl_cookies.json
```

You can also pass `--country` if you want to target another supported Lidl country; by default this project is configured for **GB / `lidl.co.uk`**.

### What the script does

- Connects to the Lidl receipts API using your authenticated session
- Collects receipt IDs (only those with a digital HTML receipt)
- Downloads and parses each receipt (date, store, items, prices, savings)
- Writes / updates `lidl_receipts.json`
- Keeps receipts **sorted by date (newest first)**

If the script is interrupted, you can simply run it again; already processed receipts are skipped.

---

## Output data

- All receipts are stored in `lidl_receipts.json` in the project root.
- Each entry contains:
  - `id`, `purchase_date`, `store`
  - `total_price`, `total_price_no_saving`
  - `saved_amount`, `lidlplus_saved_amount`, `saved_deposit` (if any)
  - `items`: name, unit price, quantity, unit (`kg` or `each`)

You can use this file directly in your own analysis pipelines or load it into tools like Pandas.

---

## Dashboard

After you’ve collected some data, you can launch the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

Then open `http://localhost:8501` in your browser.

The dashboard lets you:

- Filter by date range
- See total spend, number of receipts and savings
- Break down Lidl Plus vs regular discounts
- Visualise spending over time (daily / cumulative)
- View top 10 items by quantity or total spend

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

### Copyright Notice

```text
Shopping Analyzer - Tool to extract and manage Lidl receipt data
Copyright (C) 2025 Lukas Weihrauch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```

### What this means for you:

- **Freedom to use**: You can use this software for any purpose
- **Freedom to study**: You can examine how the program works and adapt it to your needs
- **Freedom to share**: You can redistribute copies to help others
- **Freedom to improve**: You can distribute copies of your modified versions to benefit the community

### Important AGPL-3.0 Requirements:

- **Network use = Source sharing**: If you run a modified version of this software on a server that others can access over a network, you must make the source code of your modified version available to those users
- **Share improvements**: Any modifications or derivative works must also be licensed under AGPL-3.0
- **Attribution**: You must preserve all copyright notices and license information

For the complete license terms, see the [`LICENCE.md`](./LICENCE.md) file in this repository.

---
