from urllib import request, error, parse
import json

CODE_OK = 0
CODE_INVALID_PARAMETERS = 1
CODE_INTERNAL_ERROR = 2
CODE_INVALID_FUNCTION = 3
CODE_INVALID_API_KEY = 4
TIMEOUT = 20

def batchDownload(etherpadUrl, apiKey, padIds):
  data = {
      'apikey': apiKey,
      'padIds': padIds
  }
  r = request.Request(
      '{}batchExport/markdown'.format(etherpadUrl),
      parse.urlencode(data, doseq=True).encode('ascii'),
      method='POST'
  )

  try:
    pass
    response = request.urlopen(r)
    result = response.read().decode('utf-8')
    response.close()
  except error.HTTPError:
    raise

  return handleResult(json.loads(result))


def handleResult(result):
  """Handle API call result"""
  if 'code' not in result:
    raise Exception("API response has no code")
  if 'message' not in result:
    raise Exception("API response has no message")

  if 'data' not in result:
    result['data'] = None

  if result['code'] == CODE_OK:
    return result['data']
  elif result['code'] == CODE_INVALID_PARAMETERS or result['code'] == CODE_INVALID_API_KEY:
    raise ValueError(result['message'])
  elif result['code'] == CODE_INTERNAL_ERROR:
    raise Exception(result['message'])
  elif result['code'] == CODE_INVALID_FUNCTION:
    raise Exception(result['message'])
  else:
    raise Exception("An unexpected error occurred whilst handling the response")