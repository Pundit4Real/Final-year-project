# 🎓 Blockchain Voting System

A secure, transparent, and decentralized voting platform built using **Django** and **Solidity**, integrated with the **Polygon Mainnet** via **Alchemy RPC**. It ensures tamper-proof voting processes for academic elections with a powerful admin backend.

## 📦 Core Features

### ⛓️ Blockchain Features

- 🗳 **Vote Casting**  
  Receipt hashes are securely stored on the blockchain after each vote, ensuring integrity and traceability.

- 🔐 **Anonymous Voting**  
  Voters are identified using decentralized identifiers (DIDs), ensuring privacy while securing vote receipts.

- ⛓️ **On-Chain Registration**  
  Candidates and positions are registered immutably on-chain through admin-triggered actions.

- ✅ **Sync Status Indicators**  
  Real-time sync status indicators (`✔ Synced` / `✖ Not Synced`) with timestamps reflect blockchain sync state.

- 🔒 **Tamper-Proof Vote Logs**  
  Votes, once cast and synced, are stored immutably and are view-only in the system.

---

### 🛠️ Admin Features

- 🔄 **Smart Contract Sync**  
  Admins can push candidates and positions to the smart contract directly from the admin panel.

- 🚫 **Edit/Deletion Restrictions**  
  After syncing to blockchain, editing or deleting synced data is restricted to ensure data integrity.

- 🗂️ **Off-Chain Election Management**  
  Elections remain editable off-chain, allowing flexible setup before final sync.

- 🔍 **Real-Time Sync Feedback**  
  Admin panel displays live blockchain sync status for each synced entry.


## 💡 Tech Stack

- **Backend**: Django 3.10+, Django Rest Framework
- **Blockchain**: Solidity Smart Contracts on Polygon
- **Web3**: Web3.py with Alchemy RPC
- **Database**: PostgreSQL or SQLite
- **Frontend**: Django Admin (for management)

## 📦 Folder Structure (Important Modules)

* `blockchain/`:
    * `utils.py`: Handles transaction building, signing, and Web3 setup.
    * `helpers.py`: Contains essential methods for syncing and voting logic.
    * `abi.json`: The Smart Contract Application Binary Interface.
* `elections/`:
    * `models.py`: Defines Election, Position, and Candidate data models.
    * `admin.py`: Implements blockchain synchronization actions for the admin panel.
    * `serializers.py`: DRF serializers for API data handling.
* `votes/`:
    * `models.py`: Manages vote storage and associated metadata.
    * `admin.py`: Provides a view-only interface for cast votes in the admin.


## ⚙️ How It Works

1. **Admin creates elections, positions, and candidates**.
2. Positions and Candidates are synced to the blockchain using **admin actions**.
3. Users vote through the API — each vote triggers a smart contract method call.
4. A hashed receipt of the voter's DID is sent on-chain for transparency.
5. Votes are stored off-chain in Django for analytics and speed.

## 🔁 Syncing to Blockchain

Syncing is done via Django Admin using actions:
- ✅ `Sync to Blockchain` for positions or candidates
- Status is tracked using `is_synced` and `last_synced_at`

Once synced:
- Record becomes **read-only**
- Cannot be deleted from admin

## 🔐 Security Design

- Level 400 students are automatically **disqualified** from voting or contesting.
- Only eligible users (by department/level) can vote for specific positions.
- Blockchain guarantees **immutability** of votes.

## 🌐 Smart Contract Info

- **Network**: Polygon Mainnet
- **Contract Address**: `0x754a018CEC340067896b50130C782AE4fe85B174`
- **Compiler**: Solidity `0.8.30`

## 🚀 Deployment

### 1. Setup Environment

```bash
pip install -r requirements.txt
cp .env.example .env  # Set Alchemy URL, contract address, wallet keys
```


### 2. Run the Server

```bash
python manage.py migrate
python manage.py runserver
```


### 3. Admin Access

- Login to /admin and use sync buttons for blockchain actions.

## 🔎 Future Enhancements

- Public results viewer interface

- QR code voter verification

- On-chain audit dashboard

- Gasless voting using meta-transactions

## 🤝 Contributing

- Want to contribute? Fork this repo and submit a PR. Open issues for feature suggestions or bugs.

##  📝 License
- MIT © Mohammed Ali — 2025
