# Install dependencies

```
pip3 install -r requirements.txt
```

# Running

```
chmod +x main.py
./main.py --rancher-addr https://rancher.sandbox.motus.com/v3 --rancher-key token-abc12 --rancher-secret <redacted>
```

# Running Tests
```
python3 -m unittest discover . test_*.py
```