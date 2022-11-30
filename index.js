tickerInputForm = document.querySelector('#tickerInput');
submitBtn = tickerInputForm.querySelector('button');
tickerInput = document.querySelector('#textarea');
display = document.querySelector('#display');



const BASE_URL = 'api';

submitBtn.addEventListener('click', async function (e) {
  e.preventDefault();
  let ticker = tickerInput.value.trim();
  const response = await stockRequests(ticker);
  if (!response.ok) {
    display.innerHTML = 'not found';
  } else {
    const stringData = JSON.stringify(response, null, ' ')
      .replace('[', '')
      .replace(']', '');
    display.innerHTML = stringData;
  }
  tickerInput.value = '';
  return;
});

async function stockRequests(ticker) {
  // TODO: query tickerSymbols.js, proceed if exists, return not found if not.
  // DRAFT: loop over routes to make requests:
  const getRoutes = await fetch(`${BASE_URL}/routes`);
  const routes = await getRoutes.json();

  const totalAssetsVsLiabilitiesRes = await fetch(
    `${BASE_URL}/assets_vs_liabilities?ticker=${ticker}`
  );
  const epsDilutedRes = await fetch(`${BASE_URL}/eps_diluted?ticker=${ticker}`);
  const netIncomeRes = await fetch(`${BASE_URL}/net_income?ticker=${ticker}`);
  const sharesOutstandingAndNetAssetsForCommonRes = await fetch(
    `${BASE_URL}/shares_outstanding_and_net_assets_for_common?ticker=${ticker}`
  );
  if (
    totalAssetsVsLiabilitiesRes.ok &&
    epsDilutedRes &&
    netIncomeRes &&
    sharesOutstandingAndNetAssetsForCommonRes
  ) {
    const totalAssetsVsLiabilities = await totalAssetsVsLiabilitiesRes.json();
    const epsDiluted = await epsDilutedRes.json();
    const netIncome = await netIncomeRes.json();
    const sharesOutstandingAndNetAssetsForCommon =
      await sharesOutstandingAndNetAssetsForCommonRes.json();
    const responseData = {
      ticker: ticker,
      ok: true,
      assets: totalAssetsVsLiabilities.assets_data,
      eps_diluted: epsDiluted.eps_diluted_data,
      net_income: netIncome.net_income_data,
      shares_outstanding:
        sharesOutstandingAndNetAssetsForCommon.shares_outstanding_data,
      net_assets_for_common:
        sharesOutstandingAndNetAssetsForCommon.net_assets_for_common_data,
    };
    return responseData;
  } else {
    return { data: 'no data' };
  }
}
