from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account

from brownie import (
    accounts,
    config,
    chain,
    network,
    GovernorContract,
    GovernanceToken,
    Timelock,
    Box,
    Contract,
)

from web3 import Web3

VOTING_PERIOD = 5  # 5 blocks

# Proposal
PROPOSAL_DESCRIPTION = "Proposal #1: Store 1 in the Box!"
NEW_STORE_VALUE = 5


def propose(store_value):
    account = get_account()
    args = (store_value,)
    encoded_function = Contract("Box", Box[-1], Box.abi).store.encode_input(*args)
    print(encoded_function)
    governor = GovernorContract[-1]
    box = Box[-1]
    propose_tx = governor.propose(
        [box.address],
        [0],
        [encoded_function],
        PROPOSAL_DESCRIPTION,
        {"from": account},
    )
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        tx = account.transfer(accounts[0], "0 ether")
        tx.wait(1)
    propose_tx.wait(2)  # We wait 2 blocks to include the voting delay
    # This will return the proposal ID
    print(f"Proposal state {governor.state(propose_tx.return_value)}")
    print(f"Proposal snapshot {governor.proposalSnapshot(propose_tx.return_value)}")
    print(f"Proposal deadline {governor.proposalDeadline(propose_tx.return_value)}")
    return propose_tx.return_value


def vote(proposal_id: int, vote: int):
    # 0: against, 1: For, 2: abstain
    print(f"voting yes on {proposal_id}")
    account = get_account()
    governor = GovernorContract[-1]
    tx = governor.castVoteWithReason(proposal_id, vote, "I like it", {"from": account})
    tx.wait(1)
    print(tx.events["VoteCast"])
    print(f"Proposal state {governor.state(proposal_id)}")


def queue_and_execute(store_value):
    account = get_account()
    governor = GovernorContract[-1]
    box = Box[-1]
    # time.sleep(VOTING_PERIOD + 1)
    # we need to explicity give it everything, including the description hash
    # it gets the proposal id like so:
    # uint256 proposalId = hashProposal(targets, values, calldatas, descriptionHash);
    # It's nearlly exactly the same as the `propose` function, but we hash the description
    args = (store_value,)
    encoded_function = Contract.from_abi("Box", box, Box.abi).store.encode_input(*args)
    # this is the same as ethers.utils.id(description)
    description_hash = Web3.keccak(text=PROPOSAL_DESCRIPTION).hex()
    tx = governor.queue(
        [box.address],
        [0],
        [encoded_function],
        description_hash,
        {"from": account},
    )
    tx.wait(1)
    print(box.retrieve())

def move_blocks(amount):
    for block in range(amount):
        get_account().transfer(get_account(), "0 ether")
    print(chain.height)

def main():
    proposal_id = propose(NEW_STORE_VALUE)
    print(f"Proposal ID {proposal_id}")
    # We do this just to move the blocks along
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(1)
    vote(proposal_id, 1)
    # Once the voting period is over,
    # if quorum was reached (enough voting power participated)
    # and the majority voted in favor, the proposal is
    # considered successful and can proceed to be executed.
    # To execute we must first `queue` it to pass the timelock
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(VOTING_PERIOD)
    # States: {Pending, Active, Canceled, Defeated, Succeeded, Queued, Expired, Executed }
    print(f" This proposal is currently {GovernorContract[-1].state(proposal_id)}")
    queue_and_execute(NEW_STORE_VALUE)
