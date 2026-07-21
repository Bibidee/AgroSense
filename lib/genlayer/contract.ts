// Single source of truth for the deployed AgroSenseAdvisory contract.
export const AGROSENSE_CONTRACT_ADDRESS =
  (process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ||
    "0x018282942fea51E249Df8C37D9CB66bc642CD8eC") as `0x${string}`;

export const AGROSENSE_CONTRACT_NETWORK = "GenLayer StudioNet";
export const AGROSENSE_CHAIN_ID = 61999;
export const AGROSENSE_RPC_URL  = "https://studio.genlayer.com/api";
export const AGROSENSE_EXPLORER = "https://explorer-studio.genlayer.com";

export const txUrl = (hash?: string | null) =>
  hash ? `${AGROSENSE_EXPLORER}/tx/${hash}` : null;
export const addressUrl = (addr?: string | null) =>
  addr ? `${AGROSENSE_EXPLORER}/address/${addr}` : null;
