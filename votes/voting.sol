// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

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
        string[] candidateCodes;
        mapping(string => Candidate) candidates;
    }

    mapping(string => Position) private positions;
    mapping(bytes32 => bool) public hasVoted;

    event VoteCast(
        string indexed electionCode,
        string indexed positionCode,
        string candidateCode,
        uint256 timestamp,
        bytes32 receiptHash
    );

    function addPosition(
        string memory positionCode,
        string memory title,
        string memory electionCode
    ) external {
        require(!positions[positionCode].exists, "Position already exists");

        Position storage newPosition = positions[positionCode];
        newPosition.code = positionCode;
        newPosition.title = title;
        newPosition.electionCode = electionCode;
        newPosition.exists = true;
    }

    function addCandidate(
        string memory positionCode,
        string memory candidateCode,
        string memory name
    ) external {
        require(positions[positionCode].exists, "Position does not exist");

        Position storage p = positions[positionCode];
        require(bytes(p.candidates[candidateCode].code).length == 0, "Candidate already exists");

        p.candidates[candidateCode] = Candidate(candidateCode, name, 0);
        p.candidateCodes.push(candidateCode);
    }

    function vote(
        string memory positionCode,
        string memory candidateCode,
        bytes32 receiptHash
    ) external {
        require(positions[positionCode].exists, "Invalid position");
        require(!hasVoted[receiptHash], "Receipt already used");

        Position storage p = positions[positionCode];
        require(bytes(p.candidates[candidateCode].code).length > 0, "Invalid candidate");

        p.candidates[candidateCode].voteCount += 1;
        hasVoted[receiptHash] = true;

        emit VoteCast(p.electionCode, positionCode, candidateCode, block.timestamp, receiptHash);
    }

    function getResults(
        string memory positionCode
    ) external view returns (string[] memory candidateCodes, uint256[] memory voteCounts) {
        require(positions[positionCode].exists, "Invalid position");

        Position storage p = positions[positionCode];
        uint256 len = p.candidateCodes.length;

        candidateCodes = new string[](len);
        voteCounts = new uint256[](len);

        for (uint256 i = 0; i < len; i++) {
            string memory code = p.candidateCodes[i];
            candidateCodes[i] = code;
            voteCounts[i] = p.candidates[code].voteCount;
        }
    }

    function positionExists(string memory positionCode) external view returns (bool) {
        return positions[positionCode].exists;
    }
}
