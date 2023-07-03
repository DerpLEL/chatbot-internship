class Chatbox{
    constructor(){
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.message = [];
    }

    display(){
        const {openButton, chatBox, sendButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key == "Enter"){
                this.onSendButton(chatBox)
            }
        })

        const clearButton = chatBox.querySelector('.clear__button');

        clearButton.addEventListener('click', () => this.clearChat(chatBox));
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

        clearChat(chatbox) {
            let msg1 = { name: "User", message: "hist" }
            this.message.push(msg1)
            fetch($SCRIPT_ROOT + '/predict', {
                method: 'POST',
                body: JSON.stringify({message: "hist" }),
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
            .then(r => r.json())
            .then(r =>{
                let msg2 = { name: "New Ocean's bot", message: r.answer};
                this.message.push(msg2);
                // this.updateChatText(chatbox)
                textField.value = ' '
            }).catch((error) => {
                console.error('Error:', error);
                // this.updateChatText(chatbox)
                textField.value = ''
            });
            
            this.message = [];
            this.updateChatText(chatbox)
        }    

}

const chatbox = new Chatbox();
chatbox.display()