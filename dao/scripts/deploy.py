from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account

from brownie import (
    config,
    network,
    GovernorContract,
    GovernanceToken,
    Timelock,
    Box,
)

from web3 import constants

# Governor Contract
QUORUM_PERCENTAGE = 4
# VOTING_PERIOD = 45818  # 1 week - more traditional.
# You might have different periods for different kinds of proposals
VOTING_PERIOD = 5  # 5 blocks
VOTING_DELAY = 1  # 1 block

# Timelock
# MIN_DELAY = 3600  # 1 hour - more traditional
MIN_DELAY = 1  # 1 seconds




def deploy_contracts():
    deployer = get_account()
    governance_token = (
        GovernanceToken.deploy(
            {"from": deployer},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(GovernanceToken) <= 0
        else GovernanceToken[-1]
    )
    governance_token.delegate(deployer, {"from": deployer})
    print(f"Checkpoints: {governance_token.numCheckpoints(deployer)}")
    governance_time_lock = (
        Timelock.deploy(
            MIN_DELAY,
            [],
            [],
            {"from": deployer},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(Timelock) <= 0
        else Timelock[-1]
    )
    governor = GovernorContract.deploy(
        governance_token,
        governance_time_lock,
        QUORUM_PERCENTAGE,
        VOTING_PERIOD,
        VOTING_DELAY,
        {"from": deployer},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )

def setup_governance():
    deployer = get_account()
    governance_time_lock = Timelock[-1]
    governor = GovernorContract[-1]
    # All contracts are deployed so we could set the role
    proposer_role = governance_time_lock.PROPOSER_ROLE()
    executor_role = governance_time_lock.EXECUTOR_ROLE()
    timelock_admin_role = governance_time_lock.TIMELOCK_ADMIN_ROLE()
    governance_time_lock.grantRole(proposer_role, governor, {'from': deployer})
    governance_time_lock.grantRole(executor_role, constants.ADDRESS_ZERO, {'from': deployer})
    governance_time_lock.revokeRole(timelock_admin_role, deployer, {'from': deployer})
    # deployer is no more time lock admin

def deploy_box():
    deployer = get_account()
    box = Box.deploy({'from': deployer})
    # transfer ownership to time lock
    tx = box.transferOwnership(Timelock[-1], {'from': deployer})
    tx.wait(1)

def main():
    deploy_contracts()
    setup_governance()
    deploy_box()
