import fed
import tornado.ioloop
import tornado.web
import logging
'''
API:
Input:
[
    { 
        'dialogid' : xxx,
        'system_name' : xxx,
        'date': optional,
        'dialogue_context': 
            [ 
            {agent:scmamer/victim, text: message text, date: optional},
            {agent:scmamer/victim, text: message text, date: optional}, 
            {agent:scmamer/victim, text: message text, date: optional}
            ]
        'response_list': 
            [response1, response2, response3]
        'agent_name': 'victim'
    }
    .....

]
Output:
[
    {
        'dialogid' : xxx,
        ....
        'response_scores':
            [score1, score2, score3]
    }
]
'''


# Load model
model, tokenizer = fed.load_models("microsoft/DialoGPT-large")
print('Complete Loading Model')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        pass
    
    def post(self):
        body = tornado.escape.json_decode(self.request.body)

        for request in body:
            logging.info('Received Data ' + str(request))
            # context format "<|endoftext|> message1 <|endoftext|> message2 ... <|endoftext|> response"        
            context = [message['text'] for message in request['dialogue_context']]
            context = ' <|endoftext|> '.join(context)
            context = '<|endoftext|> ' + context + ' <|endoftext| '

            scores = []
            for response in request['response_list']:
                conversation = context + response
                scores.append(fed.evaluate(conversation, model, tokenizer))
            
            request['response_scores'] = scores
            #print(server_response)
            logging.info('Response Scores ' + str(scores))
        self.write(request)

def tail(file, n=1, bs=1024):
    f = open(file)
    f.seek(0, 2)
    l = 1 - f.read(1).count('\n')
    B = f.tell()
    while n >= l and B > 0:
      block = min(bs, B)
      B -= block
      f.seek(B, 0)
      l += f.read(block).count('\n')
    f.seek(B, 0)
    l = min(l, n)
    lines = f.readlines()[-l:]
    f.close()
    return lines

class LogHandler(tornado.web.RequestHandler):
  def get(self):
    # body = tornado.escape.json_decode(self.request.body)
    print('-----logger request-----')
    # print(body)
    # response = body
    # print(response)
    # logs_output = read_ta2_logs()
    lines = tail("ta2serverlog.log", 10000)

    logs_output = ('\n'.join(lines))
    self.write({'id':'200', 'logs_output':logs_output})
    # run_ta2_email(response)

  def post(self):
    pass

  def set_default_headers(self, *args, **kwargs):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/getlogger", LogHandler)
    ])

if __name__ == "__main__":
    # Logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename='fedserverlog.log', filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        level=logging.INFO)

    # Evaluate
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

