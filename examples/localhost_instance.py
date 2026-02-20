# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Custom model instance that calls a localhost server.
"""

import os
import logging
import requests
from typing import Optional
from src.model_helpers import ModelHelpers

logging.basicConfig(level=logging.INFO)

class Localhost_Instance:
    """
    Model instance that makes calls to a local server.
    """

    def __init__(self, context: str = "You are a helpful assistant.", key: Optional[str] = None, model: str = "localhost"):
        """
        Initialize the localhost model instance.
        
        Args:
            context: The system prompt or context for the model
            key: Not used for localhost, but kept for interface compatibility
            model: Model name (default: "localhost")
        """
        self.context = context
        self.model = model
        self.debug = False
        self.server_url = "http://localhost:8000/generate"
        
        logging.info(f"Created Localhost Model. Using model: {self.model}")
    
    def set_debug(self, debug: bool = True) -> None:
        """
        Enable or disable debug mode.
        
        Args:
            debug: Whether to enable debug mode (default: True)
        """
        self.debug = debug
        logging.info(f"Debug mode {'enabled' if debug else 'disabled'}")
    
    @property
    def requires_evaluation(self) -> bool:
        """
        Whether this model requires harness evaluation.
        
        Returns:
            bool: True (requires evaluation)
        """
        return True
    
    def prompt(self, prompt: str, schema: Optional[str] = None, prompt_log: str = "", 
               files: Optional[list] = None, timeout: int = 60, category: Optional[int] = None) -> str:
        """
        Send a prompt to the localhost server and get a response.
        
        Args:
            prompt: The user prompt/query
            schema: Optional JSON schema for structured output
            prompt_log: Path to log the prompt
            files: List of expected output files
            timeout: Timeout in seconds for the API call (default: 60)
            category: Optional integer indicating the category/problem ID
            
        Returns:
            Tuple of (parsed output dict, success boolean)
        """
        # Determine if we're expecting a single file (direct text mode)
        expected_single_file = files and len(files) == 1 and schema is None
        
        # Create system prompt using ModelHelpers
        helper = ModelHelpers()
        system_prompt = helper.create_system_prompt(self.context, schema, category)
        
        if self.debug:
            logging.debug(f"Sending prompt to localhost server: {self.server_url}")
            logging.debug(f"Model: {self.model}")
            logging.debug(f"System prompt: {system_prompt}")
            logging.debug(f"User prompt: {prompt[:100]}...")
            if files:
                logging.debug(f"Expected files: {files}")
                if expected_single_file:
                    logging.debug(f"Using direct text mode for single file")
        
        # Create directories for prompt log if needed
        if prompt_log:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(prompt_log), exist_ok=True)
                
                # Write to a temporary file first
                temp_log = f"{prompt_log}.tmp"
                with open(temp_log, "w+") as f:
                    f.write(system_prompt + "\n\n----------------------------------------\n" + prompt)
                
                # Atomic rename to final file
                os.replace(temp_log, prompt_log)
            except Exception as e:
                logging.error(f"Failed to write prompt log to {prompt_log}: {str(e)}")
                # Don't continue if we can't write the log file
                raise
        
        try:
            # Make POST request to localhost server (no timeout)
            response = requests.post(
                self.server_url,
                json={
                    "prompt": prompt,
                    "model": self.model
                },
                headers={"Content-Type": "application/json"}
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response and extract the "response" field
            response_data = response.json()
            result = response_data.get("response", "")
            
            if self.debug:
                logging.debug(f"Response received from server: {result[:100]}...")
            
            # Use ModelHelpers to parse the response (already created above)
            return helper.parse_model_response(result, files, expected_single_file)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Unable to get response from localhost server: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = f"Failed to parse JSON response from server: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
