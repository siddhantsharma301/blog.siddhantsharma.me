# Understanding Gasper
This is a part of research for an ongoing project, so this is more of a braindump. 
Read the original Gasper paper [here](https://arxiv.org/pdf/2003.03052.pdf).

## Table of Contents
- [Understanding Gasper](#understanding-gasper)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Goals](#goals)
  - [Groundwork and Model](#groundwork-and-model)
  - [LMD GHOST -- v0](#lmd-ghost----v0)
  - [Detour: Committees and Block Production](#detour-committees-and-block-production)
  - [Prototype Hybrid LMD GHOST -- v0.999...](#prototype-hybrid-lmd-ghost----v0999)
  - [Hybrid LMD GHOST -- v1](#hybrid-lmd-ghost----v1)

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
  * Some nice EBB properties:
    * For all `B`, `EBB(B, 0) = genesis()`
    * If `slot(B) = jC` for some `j`, `B` is EBB in all chains that include `B`
      * AKA if block `B` is last block in epoch `j`, it’s EBB for all chains that include `B`
      * It is possible for `B` to be EBB for blocks in different epochs → why we have `(B, j)` notation

## LMD GHOST -- v0
* LMD = last message driven
* GHOST = greediest heaviest observed subtree
* LMD GHOST greedily pick blocks with most activity for next block production
  * Activity == weight == # of attestations
```
def lmdGhost(G: view) -> block:
	B = genesis()						# genesis block
	M = latestAttestations()		# one per validator
	while B not in G.leaves:
		B = argmax([weight(G, child, M) for child in B.children])
	return B
```
## Detour: Committees and Block Production
* Committees picked to propose a block at each slot
  * Slot is `i = jC+k`
  * Proposer `P` picked randomly for each slot and does runs `HLMD(view(P, i)) = B’` to propose `B’`
  * `B’` has `slot(B) = i`, `B’.parent = B`, `newattests(B)`, and other metadata
    * `newattests(B)` is all attestations for `B` and not included in `newattests(B*)` for ancestor `B*` of `B`
    * Metadata irrelevant for consensus (impl. specific)
    * If block `B` seen but parents not, `newattests(B)` ignored
  * At time `(i + ½)`, validator `V` finds `B’ = HLMD(view(V, i+½))` and make attestation `a`
    * `slot(a) = jC + k`
    * `block(a) = B’` ⇒ `a` attests to `block(a)`
    * `slot(block(a)) ≤ slot(a)`
    * Checkpoint edge = “FFG vote” between two epoch boundary pairs
* Supermajority link = if >⅔ of total validator stake in attestations linking `(A, j’) → (B, j)` (via checkpoint edge)
* Justified pairs = for a view `G`, a justified pair is
  * `J(·)` = justified pairs for view
  * If `(A, j’)` in `J(G)` and checkpoint edge from `(A, j’) → (B, j)` ⇒ `(B, j)` in `J(G)`
  * `(B_gen, 0)` in `J(G)`

## Prototype Hybrid LMD GHOST -- v0.999...
```
def protoHLMD(G: view) -> block:
	(B_j, j) = getHighestEpochJustifiedPair(G)
	B = B_j
	M = latestAttestations()
	while B not in G.leaves:
B = argmax([weight(G, child, M) for child in B.children])
return B
```

## Hybrid LMD GHOST -- v1
```
def HLMD(G: view) -> block:
	(B_j, j) = max([J(l) for l in G.leaves]) # only leaves
	B’ = [(B_j, j) in J(l) for l in G.leaves]
	B = B_j, G’ = union([chain(b) for b in B’]) 
	M = latestAttestations()
	while B not in G’.leaves:
B = argmax([weight(G’, child, M) for child in B.children])
return B
```
* Each leaf `B_l` stores state of its last justified pair
* During epoch, new attestations to blocks → update GHOST attestations `M` but NOT Casper attestations (frozen!)
  * Prevent mixing of the two with hybrid approach



