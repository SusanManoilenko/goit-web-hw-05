import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta


class CurrencyAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def fetch_currency_rate(self, session, date: str):
        url = f"{self.base_url}/{date}?json"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
        except aiohttp.ClientError as e:
            print(f"Failed to fetch data for {date}: {e}")
            return None


class PrivatBankAPI(CurrencyAPI):
    def __init__(self):
        super().__init__("https://api.privatbank.ua/p24api/exchange_rates?date")

    def extract_rates(self, data):
        if not data or 'exchangeRate' not in data:
            return None
        rates = {
            'EUR': None,
            'USD': None
        }
        for rate in data['exchangeRate']:
            if rate['currency'] in rates:
                rates[rate['currency']] = {
                    'sale': rate['saleRate'],
                    'purchase': rate['purchaseRate']
                }
        return rates


class CurrencyFetcher:
    def __init__(self, api: CurrencyAPI):
        self.api = api

    async def fetch_last_days(self, days: int):
        tasks = []
        today = datetime.now()
        async with aiohttp.ClientSession() as session:
            for i in range(days):
                date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
                tasks.append(self.api.fetch_currency_rate(session, date))

            responses = await asyncio.gather(*tasks)
            results = []
            for i, response in enumerate(responses):
                date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
                rates = self.api.extract_rates(response)
                if rates:
                    results.append({date: rates})
            return results


async def main(days):
    if days > 10:
        print("Please provide a number of days less than or equal to 10.")
        return

    api = PrivatBankAPI()
    fetcher = CurrencyFetcher(api)
    rates = await fetcher.fetch_last_days(days)
    print(rates)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: py main.py <number_of_days>")
    else:
        days = int(sys.argv[1])
        asyncio.run(main(days))
