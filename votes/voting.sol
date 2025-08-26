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
    mapping(bytes32 => bool) public hasVoted;   // tracks used receiptHashes
    mapping(bytes32 => bool) private elections;
    mapping(bytes32 => bytes32[]) private electionPositions; // NEW: track positions per election

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

    // ------------------------------
    // Election / Position / Candidate setup
    // ------------------------------
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

        // keep track of this position under its election
        electionPositions[electionCode].push(positionCode);
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
        require(
            p.candidates[candidateCode].code == bytes32(0),
            "Candidate already exists"
        );

        p.candidates[candidateCode] = Candidate(candidateCode, name, 0);
        p.candidateCodes.push(candidateCode);
    }

    // ------------------------------
    // Voting
    // ------------------------------
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
        require(
            p.candidates[candidateCode].code != bytes32(0),
            "Invalid candidate"
        );

        p.candidates[candidateCode].voteCount += 1;
        hasVoted[receiptHash] = true;

        emit VoteCast(
            p.electionCode,
            positionCode,
            candidateCode,
            block.timestamp,
            receiptHash
        );
    }

    /// @notice Cast multiple votes in one transaction (ballot-style)
    function voteBatch(
        bytes32[] calldata positionCodes,
        bytes32[] calldata candidateCodes,
        bytes32[] calldata receiptHashes
    ) external {
        require(
            positionCodes.length == candidateCodes.length &&
                candidateCodes.length == receiptHashes.length,
            "Mismatched array lengths"
        );

        for (uint256 i = 0; i < positionCodes.length; i++) {
            bytes32 pos = positionCodes[i];
            bytes32 cand = candidateCodes[i];
            bytes32 receipt = receiptHashes[i];

            require(positions[pos].exists, "Invalid position");
            require(!hasVoted[receipt], "Receipt already used");

            Position storage p = positions[pos];
            require(
                p.candidates[cand].code != bytes32(0),
                "Invalid candidate"
            );

            p.candidates[cand].voteCount += 1;
            hasVoted[receipt] = true;

            emit VoteCast(
                p.electionCode,
                pos,
                cand,
                block.timestamp,
                receipt
            );
        }
    }

    // ------------------------------
    // Query functions
    // ------------------------------
    function getResults(bytes32 positionCode)
        public
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

    /// @notice Get results for all positions in an election at once
    function getBallotResults(bytes32 electionCode)
        external
        view
        validBytes32(electionCode)
        returns (
            bytes32[] memory positionCodes,
            bytes32[][] memory allCandidateCodes,
            uint256[][] memory allVoteCounts
        )
    {
        require(elections[electionCode], "Invalid election");

        uint256 numPositions = electionPositions[electionCode].length;
        positionCodes = new bytes32[](numPositions);
        allCandidateCodes = new bytes32[][](numPositions);
        allVoteCounts = new uint256[][](numPositions);

        for (uint256 i = 0; i < numPositions; i++) {
            bytes32 posCode = electionPositions[electionCode][i];
            positionCodes[i] = posCode;

            (bytes32[] memory cands, uint256[] memory counts) = getResults(posCode);
            allCandidateCodes[i] = cands;
            allVoteCounts[i] = counts;
        }
    }

    function positionExists(bytes32 positionCode) external view returns (bool) {
        return positions[positionCode].exists;
    }

    function electionExists(bytes32 electionCode) external view returns (bool) {
        return elections[electionCode];
    }

    function candidateExists(bytes32 positionCode, bytes32 candidateCode)
        external
        view
        returns (bool)
    {
        if (!positions[positionCode].exists) return false;
        return
            positions[positionCode].candidates[candidateCode].code != bytes32(0);
    }
}
