import requests
import logging
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker
#googlegenerative
import google.generativeai as genai
#dotenv
from dotenv import load_dotenv
import os

#function
from .utils import format_nopol_for_view, extract_vehicle_plate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv('VERTEX_AI_API_KEY')
genai.configure(api_key=api_key)

class ActionCheckPajak(Action):

    def name(self):
        return "action_check_pajak"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        logger.info("ActionCheckPajak is called.")
        no_polisi = tracker.get_slot('no_polisi')
        logger.info(f"Fetching tax information for no_polisi: {no_polisi}")

        if not no_polisi:
            dispatcher.utter_message(text="Nomor polisi tidak tersedia.")
            return []
        
        nopol_getter = extract_vehicle_plate(no_polisi)
        nopol_payload = format_nopol_for_view(nopol_getter)
        if(extract_vehicle_plate(no_polisi) == None):
            dispatcher.utter_message(text="Silahkan Masukkan Plat Nomor Kendaraan")
            return []
            
        logger.info(f"Request failed: 2")
        logger.info(f"Request failed: {extract_vehicle_plate(no_polisi)}")
        logger.info(f"Request failed: 1")
        logger.info(f"Request failed: {format_nopol_for_view(extract_vehicle_plate(no_polisi))}")
        
        logger.info(f"Formatted no_polisi: {nopol_payload}")

        try:
            response = requests.get(f"http://192.168.99.195:8080/api/info-pajak/by-no-polisi?no_polisi={nopol_payload}&kd_plat=1", timeout=30)
            response.raise_for_status()  # Raise an error for bad responses
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            dispatcher.utter_message(text="Terjadi kesalahan saat menghubungi server.")
            return []

        if response.status_code == 200:
            data_pajak = response.json()
            logger.info(f"Response JSON: {data_pajak}")

            data = data_pajak.get("data")
            if isinstance(data, dict):
                besaran_pajak = data_pajak["data"].get('data_total_tagihan')
                if besaran_pajak is not None:
                    user_message = f"buat kalimat dalam bahasa Indonesia yang memberitahukan bahwa pajak yang harus dibayar wajib pajak untuk Nomor Polisi {nopol_getter} adalah senilai {besaran_pajak} dan sarankan wajib pajak untuk membayar pajak di pelayanan samsat terdekat"
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    try:
                            response = model.generate_content(user_message)
                            if response and hasattr(response, 'text'):
                                generated_text = response.text
                            else:
                                logger.error("Invalid response from model.")
                                generated_text = "Maaf, tidak ada teks yang dihasilkan."
                    except Exception as e:
                            logger.error(f"Error generating content: {e}")
                            generated_text = "Maaf, terjadi kesalahan saat memproses permintaan."

                            dispatcher.utter_message(text=generated_text)
                            return []
                    dispatcher.utter_message(text=generated_text)
                else:
                    dispatcher.utter_message(text="Data pajak tidak ditemukan.")
            else:
                dispatcher.utter_message(text="Data pajak tidak ditemukan.")
        else:
            dispatcher.utter_message(text=f"Maaf, saya tidak dapat menemukan informasi pajak untuk nomor polisi {no_polisi}.")
            logger.error(f"Failed to fetch tax information, status code: {response.status_code}")

        return []

class ActionCallGPT(Action):

    def name(self):
        return "action_call_gpt"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:
        logger.info("ActionCallGPT is called.")
        
        user_message = f"Balas dalam bahasa Indonesia: {tracker.latest_message.get('text')}"
        model = genai.GenerativeModel("gemini-1.5-flash")

        try:
            response = model.generate_content(user_message)
            if response and hasattr(response, 'text'):
                generated_text = response.text
            else:
                logger.error("Invalid response from model.")
                generated_text = "Maaf, tidak ada teks yang dihasilkan."
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            generated_text = "Maaf, terjadi kesalahan saat memproses permintaan."

        dispatcher.utter_message(text=generated_text)
        return []