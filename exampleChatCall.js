//Example API call in JavaScript for chat completions using GPT-3.5.
// Currently ChatGPT does not do a good job of translating the Python example to JavaScript code so I've added my own example to save
// any new JavaScript users potential headaches.

//First we define an async function that calls the API:

async function zukiCall(userMessage, userName) {
  const apiKey = ''; //Put your API key here.
  const apiUrl = 'https://zukijourney.xyzbot.net/v1/chat/completions';

  let prompt = ''; //Put your prompt here, if you want the model to play a character.
  
  const data = {
    model: 'gpt-3.5', //You can change the model here.
    messages: [
      {
        role: 'system', //This role instructs the AI on what to do. It's basically the main prompt.
        content: prompt,
      },
      {
        role: 'user', //This role indicates the message the user sent.
        content:
          prompt +
          '\n Here is a message a user called ' +
          userName +
          ' sent you: ' +
          userMessage, //We're also putting the prompt in the message because the API will revert to a generic response if userMessage is less than a certain length.
      },
    ],
    temperature: 0.7, //Change this to modify the responses' randomness (higher -> more random, lower -> more predictable). 
  };

  try {
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(data),
    });

    const responseData = await response.json();
    console.log(responseData); //You can log the JSON response in case you need to debug something.
    //Additionally, you can also change response.json() to response.text() for further debugging,
    //although this might break the return statement.
    
    return responseData['choices'][0]['message']['content'];
    
  } catch (error) {
    console.error('Error:', error);
  }


  //A few helpful resources if you're still stuck:
  //https://discord.gg/7rCVXUEE
  //https://platform.openai.com/docs/api-reference/chat/create


}

//Create a main function:

async function main() {
  let res = await zukiCall("What's 1 + 1?", "Sabs"); //Store the response in a variable.
  console.log(res); //Print response to the console.
}

main(); //Call the API with this function! You should see the response message in the console.


//Notice that it's not necessary that zukiCall() is an async function however I've purposely made it
// one as since the API is rate limited to a certain number of calls per minute,
// it helps to use an async function inside a setTimeOut() to limit API usage per minute.
// For example, if you only want responses to be generated every 20 seconds, using async inside a 
// setTimeOut() function makes things much easier.
