  # -*- coding=UTF-8 -*-
import hashlib
import math
import itertools
import collections
Block = collections.namedtuple("Block", ["root", "parts", "size"])
Part = collections.namedtuple("Part", ["part1", "part2", "proofs"])
Proof = collections.namedtuple("Proof", ["index", "proof"])

def split_in_fixed_size(data, fixed_size=10):
    data += "".join([" " for i in range(fixed_size-1)])
    return [data[i*fixed_size:(i+1)*fixed_size] for i in range(int(len(data)/fixed_size))]

def make_pairs(_nodes):
    nodes = iter(_nodes)
    for e in itertools.zip_longest(nodes, nodes):
        yield e

def hash_pair(pair):
    md5 = hashlib.md5()
    md5.update(pair[0].encode("utf-8"))
    md5.update(pair[1].encode("utf-8"))
    return md5.hexdigest()

def build_merkel_tree(nodes):
    start = 0
    while True:
        uplevel = []
        for pair in make_pairs(nodes[start:]):
            uplevel.append(hash_pair(pair))
        start = len(nodes)
        nodes.extend(uplevel)
        if len(uplevel) == 1:
            return nodes
    return []


def patch_balanced_btree_leaves(leaves):
    if math.pow(2, int(math.log(len(leaves), 2))) == len(leaves):
        return leaves
    btree_leaves_len = int(math.pow(2, int(1+math.log(len(leaves), 2))))
    return leaves + ["" for i in range(btree_leaves_len-len(leaves))]

def build_proof_paths(tree_len):
    proof_indexes = [0]
    for i in range(tree_len-1):
        for j in range(int(math.pow(2, i)), int(math.pow(2, i+1)), 2):
            idx = j
            father = int(j/2)
            uncle = father - 1
            if father % 2== 1:
                uncle = father+1
            if uncle < 0:
                uncle = 0
            if j>1:
                idx += 1
            proof_indexes.append([proof_indexes[uncle], idx])
            proof_indexes.append([proof_indexes[uncle], idx+1])
    proof_paths = proof_indexes[int(math.pow(2, tree_len-2))-1:int(math.pow(2, tree_len-1))-1]
    proof_paths = proof_paths[::-1]
    for i in range(0, len(proof_paths) ,2):
        proof_paths[i], proof_paths[i+1] = proof_paths[i+1], proof_paths[i]
    return proof_paths

def flatten_list(path):
     rt = []
     for e in path:
          if isinstance(e, list):
              rt.extend(flatten_list(e))
          else:
              rt.append(e)
     return rt

def build_block_parts(data):
    leaves = split_in_fixed_size(data)
    raw_leaves_len = len(leaves)
    leaves = patch_balanced_btree_leaves(leaves)
    nodes = build_merkel_tree(leaves)
    block = Block(nodes[len(nodes)-1], [], raw_leaves_len)
    leaves_len = len(leaves)
    paths = build_proof_paths(int(math.log(len(nodes)+1, 2)))
    nodes_len = len(nodes)
    leaf_pairs = list(make_pairs(leaves[:raw_leaves_len]))
    nodes = nodes[::-1]
    for i in range(int(raw_leaves_len/2)):
        path = flatten_list(paths[i])[::-1]
        proofs = [Proof(j, nodes[j]) for j in path]
        part = Part(leaf_pairs[i][0], leaf_pairs[i][1], proofs)
        block.parts.append(part)
    return block

def verif_part(part, root):
    if root != part.proofs[len(part.proofs)-1].proof:
        return False
    mediate_hash = hash_pair([part.part1, part.part2])
    proof_len = len(part.proofs)
    for idx in range(0, proof_len-1):
        pair = ([mediate_hash, part.proofs[idx].proof])
        if part.proofs[idx].index%2==0:
            pair = pair[::-1]
        mediate_hash = hash_pair(pair)
    return True if mediate_hash == root else False
