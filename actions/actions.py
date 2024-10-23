import torch
import requests
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker

logger = logging.getLogger(__name__)

class ActionGenerateWithIndoGPT(Action):

    def name(self):
        return "action_generate_with_indogpt"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        tokenizer = AutoTokenizer.from_pretrained("indobenchmark/indogpt")
        model = AutoModelForCausalLM.from_pretrained("indobenchmark/indogpt")

        user_message = tracker.latest_message['text']

        inputs = tokenizer.encode(user_message, return_tensors='pt')
        outputs = model.generate(inputs, max_length=100, num_return_sequences=1)

        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        dispatcher.utter_message(text=generated_text)
        
        return []
    

def format_nopol_for_view(input_str: str) -> str:
    if not input_str or input_str.strip() == "" or "null" in input_str:
        return " "

    groups = input_str.split(" ")

    if len(groups) == 2:
        group1 = groups[0]
        group2 = groups[1]

        alphabetic_part = ""
        numeric_part = ""

        for char in group2:
            if char.isdigit():
                numeric_part += char
            else:
                alphabetic_part += char

        return (group1.ljust(2) + alphabetic_part.ljust(3) + numeric_part.rjust(4)).upper()

    elif len(groups) == 3:
        group1 = groups[0]
        group2 = groups[1]
        group3 = groups[2]

        return (group1.ljust(2) + group3.ljust(3) + group2.rjust(4)).upper()

    elif len(groups) > 3:
        group1 = groups[0]
        group2 = groups[1]
        group3 = groups[-1]

        return (group1.ljust(2) + group3.ljust(3) + group2.rjust(4)).upper()

    else:
        return " "


class ActionCheckPajak(Action):

    def name(self):
        return "action_check_pajak"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        no_polisi = tracker.get_slot('no_polisi')
        logger.info(f"Fetching tax information for no_polisi: {no_polisi}")

        nopol_payload = format_nopol_for_view(no_polisi)
        logger.info(f"Formatted no_polisi: {nopol_payload}")

        response = requests.get(f"http://192.168.99.195:8080/api/info-pajak/by-no-polisi?no_polisi={nopol_payload}&kd_plat=1")
        
        if response.status_code == 200:
            data_pajak = response.json()
            logger.info(f"Response JSON: {data_pajak}")

            if isinstance(data_pajak["data"], dict):
                besaran_pajak = data_pajak["data"].get('data_total_tagihan')
                if besaran_pajak is not None:
                    dispatcher.utter_message(text=f"Pajak kendaraan dengan No Polisi {no_polisi} adalah {besaran_pajak} Rupiah.")
                else:
                    dispatcher.utter_message(text="Data pajak tidak ditemukan.")
            else:
                dispatcher.utter_message(text="Data pajak tidak ditemukan.")
        else:
            dispatcher.utter_message(text=f"Maaf, saya tidak dapat menemukan informasi pajak untuk nomor polisi {no_polisi}.")
            logger.error(f"Failed to fetch tax information, status code: {response.status_code}")

        return []
