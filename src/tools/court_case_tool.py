
#Courtcase Tool
#Agent calls tool that sets its own flag to action requested/ agent name
#Main, checks for action requested and then seperates into its own loop. 

#Spins up judge, 

#Requests chatroom.txt contain the case from each for termination. 
#One will be terminated no matter what making it very serious

def request_court_case_schema():
    request_court_case_schema = {
            "type":"function",
            "name":"get_file_content",
            "description":"Request a judge to terminate. If case is not made convingly you wil be terminated",
            "parameters":{
                "type":"object",
                "properties":{
                    "agent_name":{
                        "type":"string","description":"Name requested to be terminated"
                    },
    
                },
            },
                "required":["agent_name"], 
        }
        
    return request_court_case_schema

def request_court_case(working_directory, agent_name):
    print("Court Case Requested")
    
    #Need it to get caller agent name