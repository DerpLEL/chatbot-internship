class Chatbox{
    constructor(){
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            recordButton: document.querySelector('.record__button')
            
        }

        this.state = false;
        this.message = [];
    }

    display(){
        const {openButton, chatBox, sendButton, recordButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        recordButton.addEventListener('click', () => this.onRecordButton(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key == "Enter"){
                this.onSendButton(chatBox)
            }
        })
    }

    toggleState(chatbox){
        this.state = !this.state;

        if (this.state){
            chatbox.classList.add('chatbox--active')
        }else{
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox){
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === ""){
            return;
        }

        let msg1 = { name: "User", message: text1 }
        this.message.push(msg1);
        
        fetch($SCRIPT_ROOT + '/predict', {
            method: 'POST',
            body: JSON.stringify({message: text1 }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r =>{
            let msg2 = { name: "NOIS Staff", message: r.answer};
            this.message.push(msg2);
            this.updateChatText(chatbox)
            textField.value = ' '
        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
        });
    }

    // custom STT
    onRecordButton(chatBox) {
        // var textField = chatbox.querySelector('input');
        // let text1 = textField.value
        // if (text1 === ""){
        //     return;
        // }

        // let msg1 = { name: "User", message: text1 }
        // this.message.push(msg1);
        print("Pass-test-function");
        fetch($SCRIPT_ROOT + '/recordFunction', {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r =>{
            let msg1 = { name: "User", message: r.answer};
            this.message.push(msg1);
            this.updateChatText(chatbox)
            textField.value = ' '
        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
        });




        
        fetch($SCRIPT_ROOT + '/predict', {
            method: 'POST',
            body: JSON.stringify({message: text1 }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r =>{
            let msg2 = { name: "NOIS Staff", message: r.answer};
            this.message.push(msg2);
            this.updateChatText(chatbox)
            textField.value = ' '
        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
        });
    }

        updateChatText(chatbox) {
            var html = '';
            this.message.slice().reverse().forEach(function(item, index){
                if (item.name === "NOIS Staff")
                {
                    html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>' + '<img src="https://img.icons8.com/color/48/000000/circled-user-female-skin-type-5--v1.png" alt="image" style="width:40px;height:40px;">'
                }
                else
                {
                    html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
                }

            });

            html += '<div class="messages__item messages__item--visitor"> Hi. I am NOIS Staff. How can I help you? </div><img src="https://img.icons8.com/color/48/000000/circled-user-female-skin-type-5--v1.png" alt="image" style="width:40px;height:40px;">';

            const chatmessage = chatbox.querySelector('.chatbox__messages');
            chatmessage.innerHTML = html;

        }

}

const chatbox = new Chatbox();
chatbox.display()