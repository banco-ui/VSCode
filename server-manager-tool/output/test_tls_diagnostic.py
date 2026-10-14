"""Phase 1-RF.1 TLS Diagnostic Script"""
import socket
import ssl

servers = [
    {'name': 'Dell XR11', 'host': '10.254.174.17'},
    {'name': 'Dell R750', 'host': '10.254.171.113'},
    {'name': 'HPE e910t', 'host': '10.254.170.196'},
]

print("=" * 60)
print("PHASE 1-RF.1 - TLS DIAGNOSTIC")
print("=" * 60)

for srv in servers:
    print(f"\n### {srv['name']} ({srv['host']}) ###")
    
    # Step 1: TCP connectivity
    print("Step 1: TCP 443 connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((srv['host'], 443))
        if result == 0:
            print("  TCP: OPEN")
        else:
            print(f"  TCP: CLOSED (code {result})")
            sock.close()
            continue
        sock.close()
    except Exception as e:
        print(f"  TCP: ERROR - {e}")
        continue
    
    # Step 2: TLS handshake
    print("Step 2: TLS handshake (verify=True)...")
    try:
        ctx = ssl.create_default_context()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        ssock = ctx.wrap_socket(sock, server_hostname=srv['host'])
        ssock.connect((srv['host'], 443))
        cert = ssock.getpeercert()
        print("  TLS: PASS")
        san = cert.get('subjectAltName', [])
        ip_sans = [x[1] for x in san if x[0] == 'IP Address']
        print(f"  SAN (IP): {ip_sans}")
        if srv['host'] not in ip_sans:
            print(f"  WARNING: IP not in SAN")
        ssock.close()
    except ssl.SSLCertVerificationError as e:
        print(f"  TLS: FAIL - Cert Verification")
        err = str(e).lower()
        if 'self-signed' in err:
            print("  Type: SELF-SIGNED")
        elif 'unable to get local issuer' in err:
            print("  Type: UNTRUSTED CA")
        else:
            print(f"  Detail: {e}")
    except Exception as e:
        print(f"  TLS: ERROR - {type(e).__name__}: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)