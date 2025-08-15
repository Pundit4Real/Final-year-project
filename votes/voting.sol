// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

contract Voting {
    struct Candidate {
        bytes32 code;
        string name;
        uint256 voteCount;
    }

    struct Position {
        bytes32 code;
        string title;
        bytes32 electionCode;
        bool exists;
        bytes32[] candidateCodes;
        mapping(bytes32 => Candidate) candidates;
    }

    mapping(bytes32 => Position) private positions;
    mapping(bytes32 => bool) public hasVoted;
    mapping(bytes32 => bool) private elections;

    event VoteCast(
        bytes32 indexed electionCode,
        bytes32 indexed positionCode,
        bytes32 indexed candidateCode,
        uint256 timestamp,
        bytes32 receiptHash
    );

    modifier validBytes32(bytes32 value) {
        require(value != bytes32(0), "Invalid empty code");
        _;
    }

    function addElection(bytes32 electionCode)
        external
        validBytes32(electionCode)
    {
        require(!elections[electionCode], "Election already exists");
        elections[electionCode] = true;
    }

    function addPosition(
        bytes32 positionCode,
        string memory title,
        bytes32 electionCode
    )
        external
        validBytes32(positionCode)
        validBytes32(electionCode)
    {
        require(elections[electionCode], "Election does not exist");
        require(!positions[positionCode].exists, "Position already exists");

        Position storage newPosition = positions[positionCode];
        newPosition.code = positionCode;
        newPosition.title = title;
        newPosition.electionCode = electionCode;
        newPosition.exists = true;
    }

    function addCandidate(
        bytes32 positionCode,
        bytes32 candidateCode,
        string memory name
    )
        external
        validBytes32(positionCode)
        validBytes32(candidateCode)
    {
        require(positions[positionCode].exists, "Position does not exist");

        Position storage p = positions[positionCode];
        require(p.candidates[candidateCode].code == bytes32(0), "Candidate already exists");

        p.candidates[candidateCode] = Candidate(candidateCode, name, 0);
        p.candidateCodes.push(candidateCode);
    }

    function vote(
        bytes32 positionCode,
        bytes32 candidateCode,
        bytes32 receiptHash
    )
        external
        validBytes32(positionCode)
        validBytes32(candidateCode)
        validBytes32(receiptHash)
    {
        require(positions[positionCode].exists, "Invalid position");
        require(!hasVoted[receiptHash], "Receipt already used");

        Position storage p = positions[positionCode];
        require(p.candidates[candidateCode].code != bytes32(0), "Invalid candidate");

        p.candidates[candidateCode].voteCount += 1;
        hasVoted[receiptHash] = true;

        emit VoteCast(p.electionCode, positionCode, candidateCode, block.timestamp, receiptHash);
    }

    function getResults(bytes32 positionCode)
        external
        view
        validBytes32(positionCode)
        returns (bytes32[] memory candidateCodes, uint256[] memory voteCounts)
    {
        require(positions[positionCode].exists, "Invalid position");

        Position storage p = positions[positionCode];
        uint256 len = p.candidateCodes.length;

        candidateCodes = new bytes32[](len);
        voteCounts = new uint256[](len);

        for (uint256 i = 0; i < len; i++) {
            bytes32 code = p.candidateCodes[i];
            candidateCodes[i] = code;
            voteCounts[i] = p.candidates[code].voteCount;
        }
    }

    function positionExists(bytes32 positionCode) external view returns (bool) {
        return positions[positionCode].exists;
    }

    function electionExists(bytes32 electionCode) external view returns (bool) {
        return elections[electionCode];
    }

    function candidateExists(bytes32 positionCode, bytes32 candidateCode) external view returns (bool) {
        if (!positions[positionCode].exists) return false;
        return positions[positionCode].candidates[candidateCode].code != bytes32(0);
    }
}
