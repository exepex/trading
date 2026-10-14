# C4 reference vectors (story C4)

Hand computations of the maximum loss of twelve trades, to check `fno/checks/validity_money.py` to Rs 0.01
(`tests/checks/test_reference_vectors.py`). The method here differs from the code's: the worst level is
found at the strikes (the payoff is straight between strikes), where the code walks a 1-point grid. Every
number below was worked with a calculator script that imports nothing from `fno`; the values are in
`reference_vectors.json`.

The definition (frozen protocol, experiment 1, section 4): maximum loss = worst loss per unit at expiry
between the outer strikes x units + entry charges + pads (Rs 1 per unit on every leg, entry and exit) +
the exit charges at that level. Each order's charges: brokerage per order; exchange, SEBI and IPFT on the
turnover; GST on those four; STT on a sale; stamp duty on a purchase. A fill under one tick (0.05) is
charged at 0.05.

## V1. Short iron fly 25000, wings 200, no charges

Units 65; charge table: zero.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | sell | 200.00 |
| 25000 PE | sell | 200.00 |
| 25200 CE | buy | 121.30 |
| 24800 PE | buy | 121.30 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25000 CE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - sold 25000 PE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - bought 25200 CE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - bought 24800 PE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - entry charges = **0.000000**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: (0 - 200.00) + (200 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - at 25000: (0 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = -157.4000
  - at 25200: (200 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - worst loss per unit **42.6000** at 24800, 25200

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24800:
  -   sold 25000 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
    - exit charges at 24800 = **0.000000**
  - at 25200:
  -   sold 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 25000 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
    - exit charges at 25200 = **0.000000**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 42.6000 x 65 + 0.000000 + 520.00 + 0.000000 = **Rs 3289.00**

## V2. Short condor 25500/24500, wings 100, no charges

Units 65; charge table: zero.

| Leg | Side at entry | Price |
|---|---|---|
| 25500 CE | sell | 57.30 |
| 24500 PE | sell | 57.30 |
| 25600 CE | buy | 44.65 |
| 24400 PE | buy | 44.65 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25500 CE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - sold 24500 PE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - bought 25600 CE: buy at 45.65; turnover 45.65 x 65 = 2967.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - bought 24400 PE: buy at 45.65; turnover 45.65 x 65 = 2967.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - entry charges = **0.000000**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24400: (0 - 57.30) + (100 - 57.30) - (0 - 44.65) - (0 - 44.65) = 74.7000
  - at 24500: (0 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = -25.3000
  - at 25500: (0 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = -25.3000
  - at 25600: (100 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = 74.7000
  - worst loss per unit **74.7000** at 24400, 25600

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24400:
  -   sold 25500 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 24500 PE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 25600 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 24400 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
    - exit charges at 24400 = **0.000000**
  - at 25600:
  -   sold 25500 CE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 24500 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 25600 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 24400 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
    - exit charges at 25600 = **0.000000**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 74.7000 x 65 + 0.000000 + 520.00 + 0.000000 = **Rs 5375.50**

## V3. Long iron fly 25000, wings 100, no charges

Units 65; charge table: zero.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | buy | 200.00 |
| 25000 PE | buy | 200.00 |
| 25100 CE | sell | 155.75 |
| 24900 PE | sell | 155.75 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - bought 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - bought 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - sold 25100 CE: sell at 154.75; turnover 154.75 x 65 = 10058.7500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - sold 24900 PE: sell at 154.75; turnover 154.75 x 65 = 10058.7500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  - entry charges = **0.000000**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24900: - (0 - 200.00) - (100 - 200.00) + (0 - 155.75) + (0 - 155.75) = -11.5000
  - at 25000: - (0 - 200.00) - (0 - 200.00) + (0 - 155.75) + (0 - 155.75) = 88.5000
  - at 25100: - (100 - 200.00) - (0 - 200.00) + (0 - 155.75) + (0 - 155.75) = -11.5000
  - worst loss per unit **88.5000** at 25000

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 25000:
  -   bought 25000 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   bought 25000 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 25100 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
  -   sold 24900 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 0.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 0.000000 + STT 0.000000 + stamp 0.000000 = **0.000000**
    - exit charges at 25000 = **0.000000**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 88.5000 x 65 + 0.000000 + 520.00 + 0.000000 = **Rs 6272.50**

## V4. Short iron fly 25000/200, brokerage and GST only

Units 65; charge table: brokerage and GST only.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | sell | 200.00 |
| 25000 PE | sell | 200.00 |
| 25200 CE | buy | 121.30 |
| 24800 PE | buy | 121.30 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25000 CE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  - sold 25000 PE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  - bought 25200 CE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  - bought 24800 PE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  - entry charges = **94.400000**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: (0 - 200.00) + (200 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - at 25000: (0 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = -157.4000
  - at 25200: (200 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - worst loss per unit **42.6000** at 24800, 25200

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24800:
  -   sold 25000 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   sold 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
    - exit charges at 24800 = **94.400000**
  - at 25200:
  -   sold 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   sold 25000 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.000000 + SEBI 0.000000 + IPFT 0.000000 + GST 3.600000 + STT 0.000000 + stamp 0.000000 = **23.600000**
    - exit charges at 25200 = **94.400000**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 42.6000 x 65 + 94.400000 + 520.00 + 94.400000 = **Rs 3477.80**

## V5. Short iron fly 25000/200, every charge

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | sell | 200.00 |
| 25000 PE | sell | 200.00 |
| 25200 CE | buy | 121.30 |
| 24800 PE | buy | 121.30 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25000 CE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 20.0000 + exchange 4.531130 + SEBI 0.012935 + IPFT 0.064675 + GST 4.429573 + STT 19.402500 + stamp 0.000000 = **48.440814**
  - sold 25000 PE: sell at 199.00; turnover 199.00 x 65 = 12935.0000; brokerage 20.0000 + exchange 4.531130 + SEBI 0.012935 + IPFT 0.064675 + GST 4.429573 + STT 19.402500 + stamp 0.000000 = **48.440814**
  - bought 25200 CE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 20.0000 + exchange 2.784710 + SEBI 0.007949 + IPFT 0.039747 + GST 4.109833 + STT 0.000000 + stamp 0.238485 = **27.180725**
  - bought 24800 PE: buy at 122.30; turnover 122.30 x 65 = 7949.5000; brokerage 20.0000 + exchange 2.784710 + SEBI 0.007949 + IPFT 0.039747 + GST 4.109833 + STT 0.000000 + stamp 0.238485 = **27.180725**
  - entry charges = **151.243078**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: (0 - 200.00) + (200 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - at 25000: (0 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = -157.4000
  - at 25200: (200 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - worst loss per unit **42.6000** at 24800, 25200

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24800:
  -   sold 25000 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 24800 = **100.326681**
  - at 25200:
  -   sold 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  -   sold 25000 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 25200 = **100.326681**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 42.6000 x 65 + 151.243078 + 520.00 + 100.326681 = **Rs 3540.57**

## V6. Short condor 25500/24500/100, every charge

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25500 CE | sell | 57.30 |
| 24500 PE | sell | 57.30 |
| 25600 CE | buy | 44.65 |
| 24400 PE | buy | 44.65 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25500 CE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 20.0000 + exchange 1.281923 + SEBI 0.003659 + IPFT 0.018298 + GST 3.834698 + STT 5.489250 + stamp 0.000000 = **30.627828**
  - sold 24500 PE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 20.0000 + exchange 1.281923 + SEBI 0.003659 + IPFT 0.018298 + GST 3.834698 + STT 5.489250 + stamp 0.000000 = **30.627828**
  - bought 25600 CE: buy at 45.65; turnover 45.65 x 65 = 2967.2500; brokerage 20.0000 + exchange 1.039428 + SEBI 0.002967 + IPFT 0.014836 + GST 3.790302 + STT 0.000000 + stamp 0.089017 = **24.936550**
  - bought 24400 PE: buy at 45.65; turnover 45.65 x 65 = 2967.2500; brokerage 20.0000 + exchange 1.039428 + SEBI 0.002967 + IPFT 0.014836 + GST 3.790302 + STT 0.000000 + stamp 0.089017 = **24.936550**
  - entry charges = **111.128757**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24400: (0 - 57.30) + (100 - 57.30) - (0 - 44.65) - (0 - 44.65) = 74.7000
  - at 24500: (0 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = -25.3000
  - at 25500: (0 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = -25.3000
  - at 25600: (100 - 57.30) + (0 - 57.30) - (0 - 44.65) - (0 - 44.65) = 74.7000
  - worst loss per unit **74.7000** at 24400, 25600

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24400:
  -   sold 25500 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 24500 PE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 20.0000 + exchange 2.299720 + SEBI 0.006565 + IPFT 0.032825 + GST 4.021040 + STT 0.000000 + stamp 0.196950 = **26.557099**
  -   bought 25600 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24400 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 24400 = **97.398860**
  - at 25600:
  -   sold 25500 CE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 20.0000 + exchange 2.299720 + SEBI 0.006565 + IPFT 0.032825 + GST 4.021040 + STT 0.000000 + stamp 0.196950 = **26.557099**
  -   sold 24500 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   bought 25600 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24400 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 25600 = **97.398860**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 74.7000 x 65 + 111.128757 + 520.00 + 97.398860 = **Rs 5584.03**

## V7. Long iron fly 25000/100, every charge

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | buy | 200.00 |
| 25000 PE | buy | 200.00 |
| 25100 CE | sell | 155.75 |
| 24900 PE | sell | 155.75 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - bought 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  - bought 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  - sold 25100 CE: sell at 154.75; turnover 154.75 x 65 = 10058.7500; brokerage 20.0000 + exchange 3.523580 + SEBI 0.010059 + IPFT 0.050294 + GST 4.245108 + STT 15.088125 + stamp 0.000000 = **42.917165**
  - sold 24900 PE: sell at 154.75; turnover 154.75 x 65 = 10058.7500; brokerage 20.0000 + exchange 3.523580 + SEBI 0.010059 + IPFT 0.050294 + GST 4.245108 + STT 15.088125 + stamp 0.000000 = **42.917165**
  - entry charges = **144.804171**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24900: - (0 - 200.00) - (100 - 200.00) + (0 - 155.75) + (0 - 155.75) = -11.5000
  - at 25000: - (0 - 200.00) - (0 - 200.00) + (0 - 155.75) + (0 - 155.75) = 88.5000
  - at 25100: - (100 - 200.00) - (0 - 200.00) + (0 - 155.75) + (0 - 155.75) = -11.5000
  - worst loss per unit **88.5000** at 25000

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 25000:
  -   bought 25000 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 25000 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   sold 25100 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 24900 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
    - exit charges at 25000 = **94.471039**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 88.5000 x 65 + 144.804171 + 520.00 + 94.471039 = **Rs 6511.78**

## V8. Short iron fly 25000/200, two lots

Units 130; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | sell | 200.00 |
| 25000 PE | sell | 200.00 |
| 25200 CE | buy | 121.30 |
| 24800 PE | buy | 121.30 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25000 CE: sell at 199.00; turnover 199.00 x 130 = 25870.0000; brokerage 20.0000 + exchange 9.062261 + SEBI 0.025870 + IPFT 0.129350 + GST 5.259147 + STT 38.805000 + stamp 0.000000 = **73.281628**
  - sold 25000 PE: sell at 199.00; turnover 199.00 x 130 = 25870.0000; brokerage 20.0000 + exchange 9.062261 + SEBI 0.025870 + IPFT 0.129350 + GST 5.259147 + STT 38.805000 + stamp 0.000000 = **73.281628**
  - bought 25200 CE: buy at 122.30; turnover 122.30 x 130 = 15899.0000; brokerage 20.0000 + exchange 5.569420 + SEBI 0.015899 + IPFT 0.079495 + GST 4.619666 + STT 0.000000 + stamp 0.476970 = **30.761450**
  - bought 24800 PE: buy at 122.30; turnover 122.30 x 130 = 15899.0000; brokerage 20.0000 + exchange 5.569420 + SEBI 0.015899 + IPFT 0.079495 + GST 4.619666 + STT 0.000000 + stamp 0.476970 = **30.761450**
  - entry charges = **208.086155**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: (0 - 200.00) + (200 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - at 25000: (0 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = -157.4000
  - at 25200: (200 - 200.00) + (0 - 200.00) - (0 - 121.30) - (0 - 121.30) = 42.6000
  - worst loss per unit **42.6000** at 24800, 25200

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24800:
  -   sold 25000 CE: buy at 1.00; turnover 1.00 x 130 = 130.0000; brokerage 20.0000 + exchange 0.045539 + SEBI 0.000130 + IPFT 0.000650 + GST 3.608337 + STT 0.000000 + stamp 0.003900 = **23.658556**
  -   sold 25000 PE: buy at 201.00; turnover 201.00 x 130 = 26130.0000; brokerage 20.0000 + exchange 9.153339 + SEBI 0.026130 + IPFT 0.130650 + GST 5.275821 + STT 0.000000 + stamp 0.783900 = **35.369840**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 130 = 6.5000; brokerage 20.0000 + exchange 0.002277 + SEBI 0.000006 + IPFT 0.000032 + GST 3.600417 + STT 0.009750 + stamp 0.000000 = **23.612483**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 130 = 6.5000; brokerage 20.0000 + exchange 0.002277 + SEBI 0.000006 + IPFT 0.000032 + GST 3.600417 + STT 0.009750 + stamp 0.000000 = **23.612483**
    - exit charges at 24800 = **106.253362**
  - at 25200:
  -   sold 25000 CE: buy at 201.00; turnover 201.00 x 130 = 26130.0000; brokerage 20.0000 + exchange 9.153339 + SEBI 0.026130 + IPFT 0.130650 + GST 5.275821 + STT 0.000000 + stamp 0.783900 = **35.369840**
  -   sold 25000 PE: buy at 1.00; turnover 1.00 x 130 = 130.0000; brokerage 20.0000 + exchange 0.045539 + SEBI 0.000130 + IPFT 0.000650 + GST 3.608337 + STT 0.000000 + stamp 0.003900 = **23.658556**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 130 = 6.5000; brokerage 20.0000 + exchange 0.002277 + SEBI 0.000006 + IPFT 0.000032 + GST 3.600417 + STT 0.009750 + stamp 0.000000 = **23.612483**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 130 = 6.5000; brokerage 20.0000 + exchange 0.002277 + SEBI 0.000006 + IPFT 0.000032 + GST 3.600417 + STT 0.009750 + stamp 0.000000 = **23.612483**
    - exit charges at 25200 = **106.253362**

**4. Pads**: 2 x 4 legs x Rs 1 x 130 units = 1040.00

**5. Maximum loss** = 42.6000 x 130 + 208.086155 + 1040.00 + 106.253362 = **Rs 6892.34**

## V9. Far short condor 26000/24000/100: prices under the pad, charged at one tick

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 26000 CE | sell | 0.80 |
| 24000 PE | sell | 0.90 |
| 26100 CE | buy | 0.40 |
| 23900 PE | buy | 0.45 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 26000 CE: sell at -0.20 (fill -0.20 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  - sold 24000 PE: sell at -0.10 (fill -0.10 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  - bought 26100 CE: buy at 1.40; turnover 1.40 x 65 = 91.0000; brokerage 20.0000 + exchange 0.031877 + SEBI 0.000091 + IPFT 0.000455 + GST 3.605836 + STT 0.000000 + stamp 0.002730 = **23.640989**
  - bought 23900 PE: buy at 1.45; turnover 1.45 x 65 = 94.2500; brokerage 20.0000 + exchange 0.033016 + SEBI 0.000094 + IPFT 0.000471 + GST 3.606045 + STT 0.000000 + stamp 0.002828 = **23.642453**
  - entry charges = **94.495926**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 23900: (0 - 0.80) + (100 - 0.90) - (0 - 0.40) - (0 - 0.45) = 99.1500
  - at 24000: (0 - 0.80) + (0 - 0.90) - (0 - 0.40) - (0 - 0.45) = -0.8500
  - at 26000: (0 - 0.80) + (0 - 0.90) - (0 - 0.40) - (0 - 0.45) = -0.8500
  - at 26100: (100 - 0.80) + (0 - 0.90) - (0 - 0.40) - (0 - 0.45) = 99.1500
  - worst loss per unit **99.1500** at 23900, 26100

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 23900:
  -   sold 26000 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 24000 PE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 20.0000 + exchange 2.299720 + SEBI 0.006565 + IPFT 0.032825 + GST 4.021040 + STT 0.000000 + stamp 0.196950 = **26.557099**
  -   bought 26100 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 23900 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 23900 = **97.398860**
  - at 26100:
  -   sold 26000 CE: buy at 101.00; turnover 101.00 x 65 = 6565.0000; brokerage 20.0000 + exchange 2.299720 + SEBI 0.006565 + IPFT 0.032825 + GST 4.021040 + STT 0.000000 + stamp 0.196950 = **26.557099**
  -   sold 24000 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   bought 26100 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 23900 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 26100 = **97.398860**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 99.1500 x 65 + 94.495926 + 520.00 + 97.398860 = **Rs 7156.64**

## V10. Long iron fly 25000, wings 200 (over the Rs 10,000 limit)

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | buy | 200.00 |
| 25000 PE | buy | 200.00 |
| 25200 CE | sell | 121.30 |
| 24800 PE | sell | 121.30 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - bought 25000 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  - bought 25000 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  - sold 25200 CE: sell at 120.30; turnover 120.30 x 65 = 7819.5000; brokerage 20.0000 + exchange 2.739171 + SEBI 0.007820 + IPFT 0.039098 + GST 4.101496 + STT 11.729250 + stamp 0.000000 = **38.616834**
  - sold 24800 PE: sell at 120.30; turnover 120.30 x 65 = 7819.5000; brokerage 20.0000 + exchange 2.739171 + SEBI 0.007820 + IPFT 0.039098 + GST 4.101496 + STT 11.729250 + stamp 0.000000 = **38.616834**
  - entry charges = **136.203508**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: - (0 - 200.00) - (200 - 200.00) + (0 - 121.30) + (0 - 121.30) = -42.6000
  - at 25000: - (0 - 200.00) - (0 - 200.00) + (0 - 121.30) + (0 - 121.30) = 157.4000
  - at 25200: - (200 - 200.00) - (0 - 200.00) + (0 - 121.30) + (0 - 121.30) = -42.6000
  - worst loss per unit **157.4000** at 25000

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 25000:
  -   bought 25000 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 25000 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   sold 25200 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 24800 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
    - exit charges at 25000 = **94.471039**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 157.4000 x 65 + 136.203508 + 520.00 + 94.471039 = **Rs 10981.67**

## V11. Short iron fly 25000/200 with uneven prices, 75 units

Units 75; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25000 CE | sell | 212.35 |
| 25000 PE | sell | 188.10 |
| 25200 CE | buy | 126.70 |
| 24800 PE | buy | 115.25 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25000 CE: sell at 211.35; turnover 211.35 x 75 = 15851.2500; brokerage 20.0000 + exchange 5.552693 + SEBI 0.015851 + IPFT 0.079256 + GST 4.616604 + STT 23.776875 + stamp 0.000000 = **54.041279**
  - sold 25000 PE: sell at 187.10; turnover 187.10 x 75 = 14032.5000; brokerage 20.0000 + exchange 4.915585 + SEBI 0.014032 + IPFT 0.070163 + GST 4.499960 + STT 21.048750 + stamp 0.000000 = **50.548490**
  - bought 25200 CE: buy at 127.70; turnover 127.70 x 75 = 9577.5000; brokerage 20.0000 + exchange 3.354998 + SEBI 0.009577 + IPFT 0.047887 + GST 4.214243 + STT 0.000000 + stamp 0.287325 = **27.914032**
  - bought 24800 PE: buy at 116.25; turnover 116.25 x 75 = 8718.7500; brokerage 20.0000 + exchange 3.054178 + SEBI 0.008719 + IPFT 0.043594 + GST 4.159168 + STT 0.000000 + stamp 0.261562 = **27.527221**
  - entry charges = **160.031023**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24800: (0 - 212.35) + (200 - 188.10) - (0 - 126.70) - (0 - 115.25) = 41.5000
  - at 25000: (0 - 212.35) + (0 - 188.10) - (0 - 126.70) - (0 - 115.25) = -158.5000
  - at 25200: (200 - 212.35) + (0 - 188.10) - (0 - 126.70) - (0 - 115.25) = 41.5000
  - worst loss per unit **41.5000** at 24800, 25200

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24800:
  -   sold 25000 CE: buy at 1.00; turnover 1.00 x 75 = 75.0000; brokerage 20.0000 + exchange 0.026273 + SEBI 0.000075 + IPFT 0.000375 + GST 3.604810 + STT 0.000000 + stamp 0.002250 = **23.633783**
  -   sold 25000 PE: buy at 201.00; turnover 201.00 x 75 = 15075.0000; brokerage 20.0000 + exchange 5.280772 + SEBI 0.015075 + IPFT 0.075375 + GST 4.566820 + STT 0.000000 + stamp 0.452250 = **30.390293**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 75 = 3.7500; brokerage 20.0000 + exchange 0.001314 + SEBI 0.000004 + IPFT 0.000019 + GST 3.600241 + STT 0.005625 + stamp 0.000000 = **23.607202**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 75 = 3.7500; brokerage 20.0000 + exchange 0.001314 + SEBI 0.000004 + IPFT 0.000019 + GST 3.600241 + STT 0.005625 + stamp 0.000000 = **23.607202**
    - exit charges at 24800 = **101.238478**
  - at 25200:
  -   sold 25000 CE: buy at 201.00; turnover 201.00 x 75 = 15075.0000; brokerage 20.0000 + exchange 5.280772 + SEBI 0.015075 + IPFT 0.075375 + GST 4.566820 + STT 0.000000 + stamp 0.452250 = **30.390293**
  -   sold 25000 PE: buy at 1.00; turnover 1.00 x 75 = 75.0000; brokerage 20.0000 + exchange 0.026273 + SEBI 0.000075 + IPFT 0.000375 + GST 3.604810 + STT 0.000000 + stamp 0.002250 = **23.633783**
  -   bought 25200 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 75 = 3.7500; brokerage 20.0000 + exchange 0.001314 + SEBI 0.000004 + IPFT 0.000019 + GST 3.600241 + STT 0.005625 + stamp 0.000000 = **23.607202**
  -   bought 24800 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 75 = 3.7500; brokerage 20.0000 + exchange 0.001314 + SEBI 0.000004 + IPFT 0.000019 + GST 3.600241 + STT 0.005625 + stamp 0.000000 = **23.607202**
    - exit charges at 25200 = **101.238478**

**4. Pads**: 2 x 4 legs x Rs 1 x 75 units = 600.00

**5. Maximum loss** = 41.5000 x 75 + 160.031023 + 600.00 + 101.238478 = **Rs 3973.77**

## V12. Short condor 25500/24500, wings 200, every charge

Units 65; charge table: config.yaml.

| Leg | Side at entry | Price |
|---|---|---|
| 25500 CE | sell | 57.30 |
| 24500 PE | sell | 57.30 |
| 25700 CE | buy | 34.75 |
| 24300 PE | buy | 34.75 |

**1. Entry charges** (a bought leg fills at price + 1, a sold leg at price - 1):
  - sold 25500 CE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 20.0000 + exchange 1.281923 + SEBI 0.003659 + IPFT 0.018298 + GST 3.834698 + STT 5.489250 + stamp 0.000000 = **30.627828**
  - sold 24500 PE: sell at 56.30; turnover 56.30 x 65 = 3659.5000; brokerage 20.0000 + exchange 1.281923 + SEBI 0.003659 + IPFT 0.018298 + GST 3.834698 + STT 5.489250 + stamp 0.000000 = **30.627828**
  - bought 25700 CE: buy at 35.75; turnover 35.75 x 65 = 2323.7500; brokerage 20.0000 + exchange 0.814010 + SEBI 0.002324 + IPFT 0.011619 + GST 3.749031 + STT 0.000000 + stamp 0.069713 = **24.646696**
  - bought 24300 PE: buy at 35.75; turnover 35.75 x 65 = 2323.7500; brokerage 20.0000 + exchange 0.814010 + SEBI 0.002324 + IPFT 0.011619 + GST 3.749031 + STT 0.000000 + stamp 0.069713 = **24.646696**
  - entry charges = **110.549048**

**2. Loss per unit at expiry** at each strike (the payoff is straight between strikes, so the worst level between the outer strikes is a strike): loss = - sum(side x (value at expiry - price)).

  - at 24300: (0 - 57.30) + (200 - 57.30) - (0 - 34.75) - (0 - 34.75) = 154.9000
  - at 24500: (0 - 57.30) + (0 - 57.30) - (0 - 34.75) - (0 - 34.75) = -45.1000
  - at 25500: (0 - 57.30) + (0 - 57.30) - (0 - 34.75) - (0 - 34.75) = -45.1000
  - at 25700: (200 - 57.30) + (0 - 57.30) - (0 - 34.75) - (0 - 34.75) = 154.9000
  - worst loss per unit **154.9000** at 24300, 25700

**3. Exit charges at the worst level** (each leg closed at its expiry value: a bought leg sold at value - 1, a sold leg bought back at value + 1); where levels tie, the larger:
  - at 24300:
  -   sold 25500 CE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   sold 24500 PE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  -   bought 25700 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24300 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 24300 = **100.326681**
  - at 25700:
  -   sold 25500 CE: buy at 201.00; turnover 201.00 x 65 = 13065.0000; brokerage 20.0000 + exchange 4.576669 + SEBI 0.013065 + IPFT 0.065325 + GST 4.437911 + STT 0.000000 + stamp 0.391950 = **29.484920**
  -   sold 24500 PE: buy at 1.00; turnover 1.00 x 65 = 65.0000; brokerage 20.0000 + exchange 0.022769 + SEBI 0.000065 + IPFT 0.000325 + GST 3.604169 + STT 0.000000 + stamp 0.001950 = **23.629278**
  -   bought 25700 CE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
  -   bought 24300 PE: sell at -1.00 (fill -1.00 charged at the 0.05 tick); turnover 0.05 x 65 = 3.2500; brokerage 20.0000 + exchange 0.001138 + SEBI 0.000003 + IPFT 0.000016 + GST 3.600208 + STT 0.004875 + stamp 0.000000 = **23.606241**
    - exit charges at 25700 = **100.326681**

**4. Pads**: 2 x 4 legs x Rs 1 x 65 units = 520.00

**5. Maximum loss** = 154.9000 x 65 + 110.549048 + 520.00 + 100.326681 = **Rs 10799.38**
