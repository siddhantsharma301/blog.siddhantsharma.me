# Understanding Gasper
This is a part of research for an ongoing project, so this is more of a braindump. 
Read the original Gasper paper [here](https://arxiv.org/pdf/2003.03052.pdf).

## Overview
Gasper is the consensus protocol used by Ethereum. It’s composed of 2 gadgets:
1. LMD GHOST: fork-choice rule for block production  
2. Casper: finality gadget  

Validators have 2 jobs: propose blocks and make attestations

## Goals
* Resilient to very dynamic validator sets  
    * Kind of tricky  
* Byzantine fault tolerant (of course)  
* Liveness favoring: chain should keep producing blocks even if not all blocks are finalized  
    * Formalized through plausible and probable finality  
* Safety: finalized chain contains no conflicting blocks for given view  
Seems contradictory, right?
* Provides 2 ledgers: give clients choice of availability vs finality ⇒ chain resilience
  * Dynamic availability ledger: longest chain
    * Always live, safe unless network partition
  * Finalized prefix ledger of dynamic availability ledger: finalized chain
    * Always safe, live unless low participation


## Groundwork and Model
* Assume partial synchrony
* Fork-choice rule = given view `V`, return single leaf block `B` to propose
  * Forms chain from genesis to `B`
  * Helps validator deterministically produce unique chain
* Finality = set of blocks that all validators accept as a part of chain history
  * Also deterministic
  * Use attestations/votes to determine longest chain, finality, and slashable offenses
* Slot = constant number of seconds containing a block
  * 12 seconds per slot in production
  * Each slot has committee attesting to their view of head of the chain
    * 1 proposer, and all members of committee attest
* Epoch = `C` slots, used to checkpoint for finality (Casper!)
  * `C=64` in production
* Epoch-boundary pairs = 1 block/epoch is the checkpoint block for Casper
  * A block can be a checkpoint ≥1 time
  * Noted as `(B, i)` and `(B, j)` for different epochs `i` and `j`
* Epoch boundary block = for block `B` and epoch `j`, define `EBB(B, j)` as function that gets block in highest slot by epoch `j` in `chain(B)`
  * AKA gets latest justified block by epoch `j` in `chain(B)`
  * Let `LEBB(B) = max([EBB(B, j) for j in epochs])` (latest EBB in `chain(B)`)

