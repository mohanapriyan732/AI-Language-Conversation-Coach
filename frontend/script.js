
const API = "https://ai-language-conversation-coach-2.onrender.com";


let selectedLanguage = "";
let selectedScenario = "";

let threadId = "";

let mediaRecorder = null;
let audioChunks = [];

const languageFlagMap = {
    "English": "🇺🇸",
    "French": "🇫🇷",
    "Spanish": "🇪🇸",
    "Hindi": "🇮🇳",
    "Japanese": "🇯🇵",
    "German": "🇩🇪",
    "Italian": "🇮🇹",
    "Portuguese": "🇵🇹",
    "Russian": "🇷🇺",
    "Chinese (Simplified)": "🇨🇳",
    "Chinese (Traditional)": "🇹🇼",
    "Korean": "🇰🇷",
    "Arabic": "🇸🇦",
    "Turkish": "🇹🇷",
    "Dutch": "🇳🇱",
    "Polish": "🇵🇱",
    "Thai": "🇹🇭",
    "Vietnamese": "🇻🇳",
    "Indonesian": "🇮🇩",
    "Malay": "🇲🇾",
    "Bengali": "🇧🇩",
    "Urdu": "🇵🇰",
    "Punjabi": "🇮🇳",
    "Telugu": "🇮🇳",
    "Kannada": "🇮🇳",
    "Malayalam": "🇮🇳",
    "Marathi": "🇮🇳",
    "Gujarati": "🇮🇳",
    "Tamil": "🇮🇳"
};

function getFlagForLanguage(language) {
    return languageFlagMap[language] || "🌐";
}

function updateLanguageFlags() {
    document.querySelectorAll(".choice[data-language]").forEach(card => {
        const flag = card.querySelector(".flag-badge");
        if (flag) {
            flag.textContent = getFlagForLanguage(card.dataset.language);
        }
    });
}

function animateSelectedFlag(card) {
    const flag = card.querySelector(".flag-badge");
    if (flag) {
        flag.classList.remove("flag-pop");
        void flag.offsetWidth;
        flag.classList.add("flag-pop");
    }
}

updateLanguageFlags();




// ==========================
// LANGUAGE
// ==========================


document
.querySelectorAll(".choice[data-language]")
.forEach(card => {


    card.onclick = ()=>{


        document
        .querySelectorAll(".choice[data-language]")
        .forEach(c =>
            c.classList.remove("selected")
        );


        card.classList.add("selected");


        selectedLanguage =
        card.dataset.language;

        animateSelectedFlag(card);


        document
        .getElementById("scenarioSection")
        .classList
        .remove("hidden");


    };


});






// ==========================
// SCENARIO
// ==========================


document
.querySelectorAll(".scenario")
.forEach(card=>{


    card.onclick=()=>{


        document
        .querySelectorAll(".scenario")
        .forEach(c =>
            c.classList.remove("selected")
        );


        card.classList.add("selected");



        selectedScenario =
        card.innerText
        .replace(/[^a-zA-Z ]/g,"")
        .trim();



        document
        .getElementById("startBtn")
        .classList
        .remove("hidden");


    };


});







// ==========================
// START
// ==========================


document
.getElementById("startBtn")
.onclick = async()=>{


    addMessage(
        "System",
        "Connecting with Nancy AI..."
    );



    const response =
    await fetch(
        `${API}/start-session`,
        {

        method:"POST",

        headers:{
            "Content-Type":
            "application/json"
        },


        body:JSON.stringify({

            language:
            selectedLanguage,

            scenario:
            selectedScenario

        })

        });



    threadId =
    response.headers
    .get("X-Thread-ID");



    document
    .getElementById("micBtn")
    .classList
    .remove("hidden");



    playAudio(response);

};









// ==========================
// MURF AUDIO FIXED
// ==========================


async function playAudio(response){


    const text =
    await response.text();



    try{


        const chunks =
        text.trim()
        .split("\n");



        let binary = "";



        chunks.forEach(chunk=>{

            binary += atob(chunk);

        });



        const bytes =
        new Uint8Array(
            binary.length
        );



        for(
            let i=0;
            i<binary.length;
            i++
        ){

            bytes[i] =
            binary.charCodeAt(i);

        }




        const blob =
        new Blob(
            [bytes],
            {
            type:"audio/mpeg"
            }
        );



        const url =
        URL.createObjectURL(blob);



        const audio =
        new Audio(url);



        addMessage(
            "Nancy 🤖",
            "Speaking..."
        );



        await audio.play();




        audio.onended=()=>{


            addMessage(
                "System",
                "Your turn 🎤"
            );


        };


    }


    catch(err){

        console.log(
            "Audio failed",
            err
        );

    }


}









// ==========================
// RECORD
// ==========================


document
.getElementById("micBtn")
.onclick = async()=>{



    const button =
    document.getElementById("micBtn");




    if(
        mediaRecorder &&
        mediaRecorder.state==="recording"
    ){


        mediaRecorder.stop();

        button.classList.remove("is-recording");

        button.innerHTML =
        "🎤";


        return;

    }




    const stream =
    await navigator
    .mediaDevices
    .getUserMedia(
        {
        audio:true
        }
    );



    audioChunks=[];



    mediaRecorder =
    new MediaRecorder(
        stream,
        {
        mimeType:
        "audio/webm"
        }
    );




    mediaRecorder.ondataavailable =
    e=>{

        audioChunks.push(e.data);

    };





    mediaRecorder.onstop =
    ()=>{


        document
        .getElementById("submitBtn")
        .classList
        .remove("hidden");


    };



    mediaRecorder.start();



    button.classList.add("is-recording");

    button.innerHTML =
    "⏹ Stop";


};









// ==========================
// SUBMIT
// ==========================


document
.getElementById("submitBtn")
.onclick = async()=>{


    document
    .getElementById("submitBtn")
    .classList
    .add("hidden");



    const blob =
    new Blob(
        audioChunks,
        {
        type:"audio/webm"
        }
    );



    const form =
    new FormData();



    form.append(
        "audio",
        blob,
        "voice.webm"
    );



    form.append(
        "thread_id",
        threadId
    );



    addMessage(
        "You",
        "🎤 Sending voice..."
    );




    const response =
    await fetch(
        `${API}/submit-response`,
        {

        method:"POST",

        body:form

        });



    updateProgress(response);



    playAudio(response);





    if(
    response.headers
    .get("X-Session-Complete")
    ){

        setTimeout(
            getFeedback,
            3000
        );

    }


};








// ==========================
// FEEDBACK
// ==========================


async function getFeedback(){


const response =
await fetch(
`${API}/get-feedback`,
{

method:"POST",

headers:{
"Content-Type":
"application/json"
},

body:JSON.stringify({

thread_id:
threadId

})

});



const data =
await response.json();



document
.getElementById("feedback")
.innerHTML = `

<h2>
📊 Feedback
</h2>

<pre>

${JSON.stringify(
data.feedback,
null,
2
)}

</pre>

`;

}





// ==========================
// UI
// ==========================


function addMessage(
name,
text
){


const box =
document.getElementById(
"chatBox"
);



box.innerHTML +=

`
<p class="mt-3">

<b>${name}</b>:
${text}

</p>
`;



box.scrollTop =
box.scrollHeight;


}






function updateProgress(response){


const count =
response.headers
.get(
"X-Exchange-Number"
);



if(count){


document
.getElementById("exchange")
.innerText =
`${count}/5`;



document
.getElementById("progress")
.style.width =
`${count*20}%`;

}


}