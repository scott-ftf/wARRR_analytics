This is a support library of wARRR annalytic resources as part of a larger project

---

**[analyze_warrr.py](https://github.com/scott-ftf/wARRR_analytics/blob/main/analyze_warrr.py)** - requires a bscscan api key. Requests all wARRR transfers from bscscan api to find all addresses that have held wARRR. Data is ineffeceintly requested in block chunks to work around free api limits.

After all transfer data is received, uses Web3 via binance rpc to get address balances. Produces a simple text report that describes how wARRR is distributed. Stores all transfers in a json file for later evaluation. 

*note: this script checks for rr.json, which is a json array of addresses that are not currently public* 

If all transfer data was previously saved to file, import it with the filename as an argument when launching the script to skip the download process.

```BASH
python3 analyze_warrr.py transfer_events.json 
```

---

**[warrr_analysis_report.txt](https://github.com/scott-ftf/wARRR_analytics/blob/main/warrr_analysis_report.txt)** - the resulting text report from the above script as of Feb 18th, 2024 

---

**[transfer_events.json](https://github.com/scott-ftf/wARRR_analytics/blob/main/transfer_events.json)** - All wARRR transfers in json format as of Feb 18th, 2024

---

**[WarrrTransferRecorder.sol](https://github.com/scott-ftf/wARRR_analytics/blob/main/WarrrTransferRecorder.sol)** - untested solidity contract. Is likely unsafe to use in its current form. Has not been evaluted and exists only for notes. 


