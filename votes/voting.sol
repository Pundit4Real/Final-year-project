// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Voting {
    struct Candidate {
        string code;
        string name;
        uint256 voteCount;
    }

    struct Position {
        string code;
        string title;
        string electionCode;
        bool exists;
        mapping(string => Candidate) candidates;
        string[] candidateCodes;
    }

    mapping(string => Position) public positions;
    mapping(bytes32 => bool) public hasVoted;

    event VoteCast(string indexed electionCode, string indexed positionCode, string candidateCode, uint256 timestamp, bytes32 receiptHash);

    function addPosition(string memory positionCode, string memory title, string memory electionCode) public {
        require(!positions[positionCode].exists, "Position already exists");
        positions[positionCode].code = positionCode;
        positions[positionCode].title = title;
        positions[positionCode].electionCode = electionCode;
        positions[positionCode].exists = true;
    }

    function addCandidate(string memory positionCode, string memory candidateCode, string memory name) public {
        require(positions[positionCode].exists, "Position doesn't exist");
        positions[positionCode].candidates[candidateCode] = Candidate(candidateCode, name, 0);
        positions[positionCode].candidateCodes.push(candidateCode);
    }

    function vote(string memory positionCode, string memory candidateCode, bytes32 receiptHash) public {
        require(positions[positionCode].exists, "Invalid position");
        require(!hasVoted[receiptHash], "Already voted with this receipt");
        positions[positionCode].candidates[candidateCode].voteCount += 1;
        hasVoted[receiptHash] = true;
        emit VoteCast(positions[positionCode].electionCode, positionCode, candidateCode, block.timestamp, receiptHash);
    }

    function getResults(string memory positionCode) public view returns (string[] memory, uint256[] memory) {
        uint256 len = positions[positionCode].candidateCodes.length;
        string[] memory codes = new string[](len);
        uint256[] memory counts = new uint256[](len);

        for (uint256 i = 0; i < len; i++) {
            string memory code = positions[positionCode].candidateCodes[i];
            codes[i] = code;
            counts[i] = positions[positionCode].candidates[code].voteCount;
        }

        return (codes, counts);
    }
}
