// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/BEP20/IBEP20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract WarrrTransferRecorder is Ownable {
    address public wARRRTokenAddress = 0xcdaf240c90f989847c56ac9dee754f76f41c5833;
    
    struct Transfer {
        address sender;
        uint256 amount;
        uint256 timestamp;
    }
    
    mapping(uint256 => Transfer) public transfers;
    uint256 public totalTransfers;
    
    event TransferRecorded(address indexed sender, uint256 amount, uint256 timestamp);
    
    function recordTransfer(uint256 amount) external {
        require(msg.sender == wARRRTokenAddress, "Only wARRR transfers allowed");
        
        Transfer memory newTransfer = Transfer({
            sender: msg.sender,
            amount: amount,
            timestamp: block.timestamp
        });
        
        transfers[totalTransfers] = newTransfer;
        totalTransfers++;
        
        emit TransferRecorded(msg.sender, amount, block.timestamp);
    }

    function getTransfers() external view returns (Transfer[] memory) {
        Transfer[] memory allTransfers = new Transfer[](totalTransfers);
        
        for (uint256 i = 0; i < totalTransfers; i++) {
            allTransfers[i] = transfers[i];
        }
        
        return allTransfers;
    }
    
    function withdrawAll() external onlyOwner {
	    address to = 0xabf1a0039c3e5741d1c816a1685b455a06e0dad4;
	    
	    IERC20 wARRRToken = IERC20(wARRRTokenAddress);
	    uint256 balance = wARRRToken.balanceOf(address(this));
	    require(balance > 0, "No wARRR balance to withdraw");
	    
	    wARRRToken.transfer(to, balance);
	}
    
    function timestampToDateString(uint256 timestamp) public pure returns (string memory) {
        return  (timestamp == 0) ? "N/A" :  datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S');
    }
}