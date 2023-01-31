tickerInputForm = document.querySelector('#tickerInput');
submitBtn = tickerInputForm.querySelector('button');
tickerInput = document.querySelector('#textarea');
display = document.querySelector('#display');
filterForm = document.querySelector('#filter');
filterSubmitBtn = filterForm.querySelector('button');
filterInput = document.querySelector('#minValue');
filterDisplay = document.querySelector('#filter-display');

const BASE_URL = 'api';

// ----------------------------------------------------
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

filterSubmitBtn.addEventListener('click', async function (e) {
  e.preventDefault();
  let minValue = filterInput.value;
  const response = await fetch(
    `${BASE_URL}/filter?criterion=EPS&min_value=${minValue}`
  );
  if (!response.ok) {
    filterDisplay.innerHTML = 'not found';
  } else {
    const data = await response.json();
    const stringData = JSON.stringify(data, null, ' ')
      .replace('[', '')
      .replace(']', '');
    filterDisplay.innerHTML = stringData;
  }
  filterInput.value = '';
  return;
});

async function stockRequests(ticker) {
  const checkTickerReq = await fetch(`${BASE_URL}/validate?ticker=${ticker}`);
  const validTicker = await checkTickerReq.json();
  if (!validTicker.data) {
    return { data: 'no data' };
  }
  // REQUESTS
  const priceReq = await fetch(`${BASE_URL}/price?ticker=${ticker}`);
  const totalAssetsVsLiabilitiesCurrRes = await fetch(
    `${BASE_URL}/assets_vs_liabilities_current?ticker=${ticker}`
  );
  const totalAssetsVsLiabilitiesRes = await fetch(
    `${BASE_URL}/assets_vs_liabilities?ticker=${ticker}`
  );
  const epsDilutedRes = await fetch(`${BASE_URL}/eps_diluted?ticker=${ticker}`);
  const netIncomeRes = await fetch(`${BASE_URL}/net_income?ticker=${ticker}`);
  const incomeTaxesRes = await fetch(
    `${BASE_URL}/income_taxes?ticker=${ticker}`
  );
  const interestPaidRes = await fetch(
    `${BASE_URL}/interest_paid?ticker=${ticker}`
  );
  const sharesOutstandingAndNetAssetsForCommonRes = await fetch(
    `${BASE_URL}/shares_outstanding_and_net_assets_for_common?ticker=${ticker}`
  );
  // JSON RESPONSES
  const price = await priceReq.json();
  const totalAssetsVsLiabilitiesCurrent =
    await totalAssetsVsLiabilitiesCurrRes.json();
  const totalAssetsVsLiabilities = await totalAssetsVsLiabilitiesRes.json();
  const epsDiluted = await epsDilutedRes.json();
  const netIncome = await netIncomeRes.json();
  const incomeTaxes = await incomeTaxesRes.json();
  const interestPaid = await interestPaidRes.json();
  const sharesOutstandingAndNetAssetsForCommon =
    await sharesOutstandingAndNetAssetsForCommonRes.json();

  // FILL DATA:
  const responseData = {
    ticker: ticker,
    price: price.price,
    ok: true,
    assets: totalAssetsVsLiabilities.assets_data,
    assets_to_liabilities_current:
      totalAssetsVsLiabilitiesCurrent.assets_to_liabilities_current_data,
    long_term_debt: totalAssetsVsLiabilitiesCurrent.long_term_debt_millified,
    eps: {
      eps_diluted: epsDiluted.eps_diluted_data,
      avg_eps_last_3_years: epsDiluted.avg_eps_last_3_years,
      price_to_avg_eps_last_3_years_ratio:
        epsDiluted.price_to_avg_eps_last_3_years_ratio,
      eps_growth_avg_10_years_by_3: epsDiluted.eps_growth_avg_10_years_by_3,
      eps_growth_avg_10_years_beginning_and_end:
        epsDiluted.eps_growth_avg_10_years_beginning_and_end,
    },
    net_income: netIncome.net_income_data,
    income_taxes: incomeTaxes.income_taxes_data,
    interest_paid: interestPaid.interest_paid_data,
    shares_outstanding:
      sharesOutstandingAndNetAssetsForCommon.shares_outstanding_data,
    net_assets_for_common:
      sharesOutstandingAndNetAssetsForCommon.net_assets_for_common_data,
  };
  return responseData;
}
