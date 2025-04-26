import requests
import lancedb
from .formatting import format_ordinance

def get_current_weather(latitude, longitude):
    # Format the URL with proper parameter substitution
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m&hourly=temperature_2m&daily=sunrise,sunset&timezone=auto"

    try:
        # Make the API call
        response = requests.get(url)

        # Raise an exception for bad status codes
        response.raise_for_status()

        # Return the JSON response
        return response.json()

    except requests.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Error fetching weather data: {e}")
        return None

class search_ordinance_or_regulation_tool:
    def __init__(self, ordinanceTable: lancedb.table.Table):
        self.ordinanceTable = ordinanceTable

    def get_tool_name(self):
        return "get_ordinance_or_regulation"

    def get_function_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "get_ordinance_or_regulation",
                "description": "Get a sepecific section of a ordinance or regulation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cap_no": {
                            "type": "string",
                            "description": "The cap_no of the ordinance or regulation (a number or a number followed by a letter)",
                        },
                        "section_no": {
                            "type": "string",
                            "description": "The section_no of the ordinance or regulation (a number or a number followed by a letter)",
                        },
                    },
                    "required": ["cap_no", "section_no"],
                },
            },
        }
    
    def run_tool(self, cap_no = None, section_no = None):
        if cap_no is None or section_no is None:
            return "No result: Missing required arguments"

        try:
            # print("Searching for ordinance or regulation...")
            # print("SQL:", "cap_no = '{}' AND section_no LIKE '{}_%'".format(cap_no, section_no))\
            
            result = self.ordinanceTable.search().where("cap_no = '{}' AND section_no = '{}'".format(cap_no, section_no)).select(["cap_no", "section_no", "type", "cap_title", "section_heading", "text", "url"]).to_list()
            if len(result) == 0:
                result = self.ordinanceTable.search().where("cap_no = '{}' AND section_no LIKE '{}_%'".format(cap_no, section_no)).select(["cap_no", "section_no", "type", "cap_title", "section_heading", "text", "url"]).to_list()


            ordinances = format_ordinance(result)
            # print("Result:", ordinances)
            return ordinances
        except Exception as e:
            print(f"Error in search_ordinance_or_regulation_tool: {e}")
            raise e


class search_cases_tool:
    def __init__(self, judgementTable: lancedb.table.Table):
        self.judgementTable = judgementTable

    def get_tool_name(self):
        return "get_case"

    def get_function_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "get_case",
                "description": "Get a sepecific case or judgment detail from the case Action No",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_no": {
                            "type": "string",
                            "description": "The action number of the case in the form of, four letter court name abreviation, followed space then case number/year. E.g. 'FACV 12/2022'",
                        },
                        "case_name": {
                            "type": "string",
                            "description": "The name of the case in the form of 'Plaintiff v. Defendant', names in capital letters.",
                        },
                    },
                    "required": [],
                },
            },
        }
    
    def run_tool(self, case_name = None, action_no = None):
        if action_no is None and case_name is None:
            return "No result: Missing required arguments"

        try:
            # print("Searching for ordinance or regulation...")
            # print("SQL:", "cap_no = '{}' AND section_no LIKE '{}_%'".format(cap_no, section_no))\
            
            result = self.judgementTable.search().where("case_name = '{}' OR case_number = '{}'".format(case_name, action_no.upper())).select(["crime_name", "case_type", "court", "case_name","case_summary","date","case_number", "case_causes", "court_decision", "url"]).to_list()

            ordinances = format_ordinance(result)
            # print("Result:", ordinances)
            return ordinances
        except Exception as e:
            print(f"Error in search_ordinance_or_regulation_tool: {e}")
            raise e