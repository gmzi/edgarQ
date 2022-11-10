tickerInputForm = document.querySelector('#tickerInput')
submitBtn = tickerInputForm.querySelector('button')
tickerInput = document.querySelector('#textarea')
display = document.querySelector('#display')

submitBtn.addEventListener('click', async function(e){
    e.preventDefault()
    let ticker = tickerInput.value
    const response = await fetch(`http://localhost:3000/api/data?ticker=${ticker}`)
    if (!response.ok){
        display.innerHTML = "not found"
    } else {
        const data = await response.json()
        const stringData = JSON.stringify(data, null,' ').replace('[', '').replace(']', '')
        display.innerHTML = stringData
    }
    tickerInput.value = '';
    return;
})