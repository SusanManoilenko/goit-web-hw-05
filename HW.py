import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta

# Базовий клас для роботи з API курсів валют
class CurrencyAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url

    # Асинхронний метод для отримання курсу валюти на конкретну дату
    async def fetch_currency_rate(self, session, date: str):
        url = f"{self.base_url}/{date}?json"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()  # Повертає JSON відповідь, якщо статус 200
                else:
                    response.raise_for_status()  # Викликає виключення, якщо статус не 200
        except aiohttp.ClientError as e:
            print(f"Failed to fetch data for {date}: {e}")
            return None

# Клас для роботи з API ПриватБанку
class PrivatBankAPI(CurrencyAPI):
    def __init__(self):
        super().__init__("https://api.privatbank.ua/p24api/exchange_rates?date")

    # Метод для витягання курсів валют з отриманих даних
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

# Клас для отримання курсів валют за кілька днів
class CurrencyFetcher:
    def __init__(self, api: CurrencyAPI):
        self.api = api

    # Асинхронний метод для отримання курсів валют за останні кілька днів
    async def fetch_last_days(self, days: int):
        tasks = []
        today = datetime.now()
        async with aiohttp.ClientSession() as session:
            for i in range(days):
                date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
                tasks.append(self.api.fetch_currency_rate(session, date))

            responses = await asyncio.gather(*tasks)  # Виконує всі задачі паралельно
            results = []
            for i, response in enumerate(responses):
                date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
                rates = self.api.extract_rates(response)
                if rates:
                    results.append({date: rates})
            return results

# Основна асинхронна функція
async def main(days):
    if days > 10:
        print("Please provide a number of days less than or equal to 10.")
        return

    api = PrivatBankAPI()
    fetcher = CurrencyFetcher(api)
    rates = await fetcher.fetch_last_days(days)
    print(rates)

# Точка входу у програму
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: py main.py <number_of_days>")
    else:
        days = int(sys.argv[1])
        asyncio.run(main(days))

