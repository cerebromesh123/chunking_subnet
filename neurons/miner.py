# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2024 VectorChat

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import time
from typing import List, Tuple
import bittensor as bt

# Bittensor Miner Template:
import chunking

# import base miner class which takes care of most of the boilerplate
from chunking.base.miner import BaseMinerNeuron
from langchain.text_splitter import NLTKTextSplitter

class Miner(BaseMinerNeuron):

    def __init__(self):
        super(Miner, self).__init__()
        self.splitter = NLTKTextSplitter()
        # TODO(developer): Anything specific to your use case you can do here

    async def forward(
        self, synapse: chunking.protocol.chunkSynapse
    ) -> chunking.protocol.chunkSynapse:
        """
        Processes the incoming chunkSynapse and returns response.

        Args:
            synapse (chunking.protocol.chunkSynapse): The synapse object containing the document.

        Returns:
            chunking.protocol.chunkSynapse: The synapse object with the 'chunks' field set to the generated chunks.

        """
        # TODO(developer): Replace with actual implementation logic.
        document = self.splitter.split_text(synapse.document)[0].split('\n\n')
        bt.logging.info(f"Received chunkSynapse: {document[0]}")
        chunks = []        
        while len(document) > 0:
            chunks.append(document[0])
            del document[0]
            while len(document) > 0 and chunks[len(chunks) - 1].count(" ") < synapse.maxTokensPerChunk:
                chunks[len(chunks) -1] += (" " + document[0])
                del document[0]
        synapse.chunks = chunks
        return synapse
    async def verify(
        self, synapse: chunking.protocol.chunkSynapse
    ) -> None:
        bt.logging.info("VERIFYING")
    async def blacklist(
        self, synapse: chunking.protocol.chunkSynapse
    ) -> Tuple[bool, str]:
        bt.logging.info("BLACKLISTING")
        """
        Determines whether an incoming request should be blacklisted and thus ignored. Your implementation should
        define the logic for blacklisting requests based on your needs and desired security parameters.

        Blacklist runs before the synapse data has been deserialized (i.e. before synapse.data is available).
        The synapse is instead contructed via the headers of the request. It is important to blacklist
        requests before they are deserialized to avoid wasting resources on requests that will be ignored.

        Args:
            synapse (chunking.protocol.chunkSynapse): A synapse object constructed from the headers of the incoming request.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the synapse's hotkey is blacklisted,
                            and a string providing the reason for the decision.

        This function is a security measure to prevent resource wastage on undesired requests. It should be enhanced
        to include checks against the metagraph for entity registration, validator status, and sufficient stake
        before deserialization of synapse data to minimize processing overhead.

        Example blacklist logic:
        - Reject if the hotkey is not a registered entity within the metagraph.
        - Consider blacklisting entities that are not validators or have insufficient stake.

        In practice it would be wise to blacklist requests from entities that are not validators, or do not have
        enough stake. This can be checked via metagraph.S and metagraph.validator_permit. You can always attain
        the uid of the sender via a metagraph.hotkeys.index( synapse.dendrite.hotkey ) call.

        Otherwise, allow the request to be processed further.
        """
        # TODO(developer): Define how miners should blacklist requests.
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if (
            not self.config.blacklist.allow_non_registered
            and synapse.dendrite.hotkey not in self.metagraph.hotkeys
        ):
            # Ignore requests from un-registered entities.
            bt.logging.debug(
                f"Blacklisting un-registered hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        if self.config.blacklist.force_validator_permit:
            # If the config is set to force validator permit, then we should only allow requests from validators.
            if not self.metagraph.validator_permit[uid]:
                bt.logging.warning(
                    f"Blacklisting a request from non-validator hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Non-validator hotkey"

        bt.logging.debug(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def priority(self, synapse: chunking.protocol.chunkSynapse) -> float:
        bt.logging.info("PRIORITIZING")
        """
        The priority function determines the order in which requests are handled. More valuable or higher-priority
        requests are processed before others. You should design your own priority mechanism with care.

        This implementation assigns priority to incoming requests based on the calling entity's stake in the metagraph.

        Args:
            synapse (chunking.protocol.chunkSynapse): The synapse object that contains metadata about the incoming request.

        Returns:
            float: A priority score derived from the stake of the calling entity.

        Miners may recieve messages from multiple entities at once. This function determines which request should be
        processed first. Higher values indicate that the request should be processed first. Lower values indicate
        that the request should be processed later.

        Example priority logic:
        - A higher stake results in a higher priority value.
        """
        # TODO(developer): Define how miners should prioritize requests.
        caller_uid = self.metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        )  # Get the caller index.
        prirority = float(
            self.metagraph.S[caller_uid]
        )  # Return the stake as the priority.
        bt.logging.debug(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return 1.0

    def save_state(self):
        pass

    def load_state(self):
        pass
        
# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(10)
