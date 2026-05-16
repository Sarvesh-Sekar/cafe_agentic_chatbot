from src.utils.custom_app_exception import CustomAppException
from settings import config
from langchain.agents import create_agent
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.resources import load_mcp_resources 
from src.models.chat_model import OrderDetails,MenuResponse,ChatResponse,NeedContextResponse
from settings import config
from langchain.agents.middleware.summarization import SummarizationMiddleware
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from typing import Literal, Union
from langgraph.types import Command


from langchain.agents.structured_output import (
    ToolStrategy,
    StructuredOutputValidationError,
    MultipleStructuredOutputsError,
)
import uuid



class Agent:
        

        def __init__(self):
                self.tools = []
                self.client = None
                self.agent = None
                self.resources = {}
                self.resource_uri = ''
                self.prompts = {}
                self.context = ""
                self.llm = None
                self.system_prompt = """ """

        
        async def get_llm(self, max_tokens: int = None, temperature: float = None):
            try:
                max_tokens = max_tokens or 3000
                temperature = temperature or 0

                llm = ChatBedrock(
                    model=config.model_id,
                    region_name="us-east-1",
                    provider="amazon",
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                self.llm = llm
            except Exception as e:

                raise CustomAppException(
                    message=f"Failed to initialise LLM client: {str(e)}",
                    status_code=500,
                    err_code="LLM_INIT_ERROR",
                )
        
        def summarizer_middleware(self):
             return SummarizationMiddleware(
                     model=self.llm,
                     trigger=("tokens",1000),
                     keep=("messages",20)
                    
)
        async def create_client(self):
             try: 
                 
                 mcp_client = MultiServerMCPClient(
                      {
                           "tools":{
                                "transport":"streamable_http",
                                "url":config.mcp_server_url
                           }
                      }
                 ) 

                 self.client = mcp_client

                 
             except CustomAppException:
                  raise
             except Exception as e:
                raise CustomAppException(
                    message=f"Failed to initialize mcp client: {str(e)}",
                    status_code=500,
                    err_code="MCP_CLIENT_INIT_ERROR",
                )
             
        async def load_tools(self):
             
             try:
                  if self.resource_uri:
                    self.tools = []
                  else:
                    self.tools = await self.client.get_tools()
                    print(self.tools,'tools')
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                            message=f"Failed to load tools: {str(e)}",
                            status_code=500,
                            err_code="LOAD_TOOL_ERR",
                  )
        async def load_resources(self):
             
             try:
                  
                  resources = await self.client.get_resources()
                  self.resources = {str(blob.metadata['uri']): str(blob.data) for blob in resources}
                    #    print(blob,'blob')
                  print('resources',self.resources)
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                            message=f"Failed to load tools: {str(e)}",
                            status_code=500,
                            err_code="LOAD_RESOURCE_ERR",
                  )
        
        async def load_prompts(self,message:str):
             
             try:

                         
                    async with self.client.session("tools") as session:
                         prompts_list = await session.list_prompts()
                         
                         for prompt_info in prompts_list.prompts:
                              # Fetch the actual prompt content
                              sample_prompt = await self.client.get_prompt(
                                   server_name="tools",
                                   prompt_name=prompt_info.name
                              )
                              
                              # sample is usually a list of Messages. 
                              # We take the first message's content and map it to the prompt name.
                              if sample_prompt:
                                   self.prompts[prompt_info.name] = sample_prompt[0].content

                    MENU_KEYWORDS = ["menu", "items", "coffee", "latte", "espresso", "price", "available"]

                    user_msg = message.lower()


                    if any(word in user_msg for word in MENU_KEYWORDS):

                         self.system_prompt = self.prompts.get('system_prompt')

                    else:
                         self.system_prompt = self.prompts.get('system_prompt')
                    
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                            message=f"Failed to load prompts: {str(e)}",
                            status_code=500,
                            err_code="LOAD_PROMPTS_ERR",
                  )
        
        async def load_context(self,message:str):
             
             try:
                    MAKING_TIPS_KEYWORDS = ["preparation", "make", "prepare", "info", "tips"]
                    POLICY_KEYWORDS = ["policy", "return", "hours", "refund", "store", "shop"]

                    user_message = message.lower()

                    if any(word in user_message for word in MAKING_TIPS_KEYWORDS):
                         self.resource_uri = "resource://get_info"
                         print("Selecting: Preparation Tips Resource")
                    elif any(word in user_message for word in POLICY_KEYWORDS):
                         self.resource_uri = "resource://get_policy_info"
                         print("Selecting: Shop Policy Resource")
                    else:
                         self.resource_uri = ''
                         print("No matching keywords found. Resource remains empty.")
                         print(self.prompts,'last_prompts')

                    if self.resource_uri:
                         self.context = self.resources[self.resource_uri]
                         self.system_prompt = self.system_prompt + "\n" + "Context: \n" + self.context
                         print(self.system_prompt)
                         self.tools = []

             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                            message=f"Failed to load context: {str(e)}",
                            status_code=500,
                            err_code="LOAD_CONTEXT_ERR",
                  )
        
        
        async def load_memory(self,message,session_id:str,customer_id:str,decisions:list):
             try:
                    DATABASE_URL = (
                    f"postgresql://{config.db_username}:{config.db_password}"
                    f"@{config.db_host}:{config.db_port}/{config.db_name}"
                    )


                    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
                         await checkpointer.setup()
                         
                         
                         if not session_id:
                              session_id = uuid.uuid4()
                         
                         session_config = {"configurable": {"thread_id": str(session_id)}}
                         
                         if session_id:
                              existing_state = await checkpointer.aget(session_config)
                              print(existing_state,'state')
                              real_messages = (existing_state["channel_values"].get('messages',[]) if existing_state and "channel_values" in existing_state else [])
                              print(real_messages,'real messages')
                         
                         
                         await self.create_agent(checkpointer=checkpointer)
                         
                         message = message + '\n' + f'customer_id of the customer is {customer_id}'
                         agent_response = await self.run_agent(message=message,session_config=session_config,decisions=decisions)

                         # for i in agent_response['messages']:
                         #      if i.additional_kwargs.get("lc_source") == "summarization":
                         #           print(i.content,'msg')
                         
                         return agent_response
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                       message=f"Failed to create Agent : {str(e)}",
                       status_code=500,
                       err_code="LOAD_ERR"
                  )

        def state_modifier(self,state):
             try:
                  messages = state['messages']
                  summary_context = ""
                  for msg in messages:
                    if (
                         isinstance(msg, HumanMessage)
                         and msg.additional_kwargs.get("lc_source") == "summarization"
                    ):
                         summary_context = f"\n\n[CONVERSATION SUMMARY]\n{msg.content}"
                         break  # only need the first/most recent summary
                  print(summary_context,'summary_context')  
                  print(SystemMessage(content=self.system_prompt + '\n' + summary_context) ,'final')
                  return SystemMessage(content=self.system_prompt + '\n' + summary_context)



             except CustomAppException :
                  raise
             except Exception as e:
                    raise CustomAppException(
                       message=f"Failed to create Agent : {str(e)}",
                       status_code=500,
                       err_code="AGENT_CREATE_ERR"
                  )
                   
        async def create_agent(self,checkpointer):
             try:

                    agent = create_agent(
                         model = self.llm,
                         tools = self.tools,
                         checkpointer=checkpointer,
                         middleware=[self.summarizer_middleware(),HumanInTheLoopMiddleware(
                              interrupt_on={"add_order": True}
                         )],
                         response_format=ToolStrategy(
                         schema = Union[OrderDetails,MenuResponse,ChatResponse,NeedContextResponse],
                         tool_message_content="Structured report captured successfully.",
                         handle_errors=True,
                                            ),
                         system_prompt = SystemMessage(self.system_prompt)
                    )
                    self.agent = agent
                    return agent
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                       message=f"Failed to create Agent : {str(e)}",
                       status_code=500,
                       err_code="AGENT_CREATE_ERR"
                  )
             
        
        async def run_agent(self,message,session_config:str,thread_id:str = None,decisions:list = None):
             try:
               
               print("decisions",decisions)
               if not decisions:
                    agent_response = await self.agent.ainvoke({"messages": HumanMessage(content=message)},config=session_config, version="v2")
               else :
                    agent_response = await self.agent.ainvoke(Command(resume={"decisions": [{"type": decisions[0].interrupt_action}]}), config=session_config)

    
                 
               print(agent_response,'agent respond')

               if hasattr(agent_response, 'interrupts'):
                    first_interrupt = agent_response.interrupts[0]
               
               
                    if 'action_requests' in first_interrupt.value:
                         action_requests = first_interrupt.value.get('action_requests', [])

                         if action_requests:
                              
                              tool_name = action_requests[0].get('name')
                              
                              return {
                                   "tool_name": tool_name,
                                   "thread_id":str(thread_id)
                              }
                    

               return agent_response
                  
             except CustomAppException:
                  raise
             except Exception as e:
                  raise CustomAppException(
                       message=f"Failed to run agent : {str(e)}",
                       status_code=500,
                       err_code="RUN AGENT ERR"
                  )
                  
        

