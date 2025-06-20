<!--
Add copywrite
-->

# Tags

# CMP Test Tags

## Protocol Core

### Message Types
| Tag | Description |
|-----|-------------|
| cr | Certificate Request message tests |
| cp | Certification Response message tests |
| ir | Initial Registration message tests |
| ip | Initial Response message tests |
| kur | Key Update Request message tests |
| kup | Key Update Response message tests |
| rr | Revocation Request message tests |
| crr | Certificate Response message tests |
| p10cr | PKCS#10 Certificate Request tests |
| certConf | Tests related to Certificate Confirmation messages |
| general-message | General message handling tests |
| support-messages | Supporting message type tests |

### Message Components
| Tag | Description |
|-----|-------------|
| PKIBody | PKI message body handling tests |
| header | Tests focusing on PKIMessage header components |--
| pvno | Tests focusing on the pvno field |
| sender | Sender field handling tests |
| senderKID | Sender Key Identifier handling tests |
| messageTime | MessageTime Field tests |
| senderNonce | Sender nonce handling tests |
| recipNonce | Recipient nonce handling tests |
| implicit_confirm | Tests for implicit confirmation handling |

## Certificate Management
### Certificate Operations
| Tag | Description |
|-----|-------------|
| certTemplate | Certificate template handling tests |
| certReqID | Certificate Request ID handling tests |
| issuing | Basic certificate issuing tests |
| issuing-advanced | Advanced certificate issuing scenarios |
| update | Certificate update operations tests |
| get_cert_template | Certificate template retrieval operations tests |
| get_root_ca_cert_update | Root CA certificate update procedures tests |
| status | Certificate status handling tests |
| ca-certs | CA certificate handling tests |
| csr | Certificate Signing Request tests |


### Certificate Content
| Tag | Description |
|-----|-------------|
| subject | Subject field handling tests |
| null-dn | Null Distinguished Name handling tests |
| add-info | Additional information field tests |
| generalInfo | General information field tests |
| extraCert | Extra certificate handling tests |
| validity | Certificate validity handling tests |
| CRLReason | Certificate Revocation List reason handling tests |
| transactionId | Transaction ID handling tests |
| regToken | Registration token tests |


### Certificate Extensions
| Tag | Description |
|-----|-------------|
| basic-constraints | Basic constraints extension tests |
| extended-key-usage | Extended key usage extension tests |
| extension | General extension handling tests |
| key-usage | Key usage extension tests |
| san | Subject Alternative Name extension tests |


## Error Handling
| Tag | Description |
|-----|-------------|
| badCertId | Reference to an unknown certificate |
| badPOP | Invalid Proof-of-Possession tests |
| certRevoked | Revocation of already revoked certificate |
| badCertTemplate | Invalid certificate template tests |
| transactionIdInUse | TransaktionID is already in use |
| notAuthorized | Unauthorized access tests |
| systemUnavail | Back-end system is currently not available |
| systemFailure | Back-end system is not functioning correctly |
| bad-behaviour | Incorrect behavior handling tests |
| badAlg | Invalid algorithm handling tests |
| badSenderNonce | 
| badRecipientNonce | 
| wrongIntegrity |
| badMessageCheck | 
| signerNotTrusted |
| badDataFormat |
| unsupportedVersion |
| badRequest | 

## Certificate Lifecycle
| Tag | Description |
|-----|-------------|
| revocation | Certificate revocation tests |
| revive | Certificate revival tests |
| publication | Certificate publication tests |
| rejection | Request rejection handling tests |


## Security
### Protection 
| Tag | Description |
|-----|-------------|
| protection | Message protection tests |
| protectionAlg | Protection algorithm tests |
| adding-protection | Protection mechanism addition tests |
| raVerified | RA verification tests |

### Authentication
| Tag | Description |
|-----|-------------|
| challenge | Basic challenge mechanism tests |
| challenge-response | Challenge-response protocol tests |
| controls | Control message handling tests |
| popo | Proof-of-Possession tests |
| sig-popo | Signature-based Proof-of-Possession tests |

### Encryption
| Tag | Description |
|-----|-------------|
| envelopedData | CMS EnvelopedData structure tests |
| encrValue | Encrypted value processing tests |
| encryptedKey | Encrypted key handling tests |


## Cryptography
### Key Operations
| Tag | Description |
|-----|-------------|
| key | Generic key operation tests |
| keyAgree | Key agreement protocol tests |
| keyEnc | Key encryption operation tests |
| kga | Key generation and archival tests |
| non-signing-key | Non-signing key handling tests |
| ak | Authorization key handling tests |
| kari | Key Agreement Recipient Info handling tests |
| ktri | Key Transport Recipient Info handling tests |
| pwri | Password Recipient Info handling tests |

### Traditional Cryptography
| Tag | Description |
|-----|-------------|
| crypto | General cryptographic operation tests |
| rsa | RSA cryptography specific tests |
| ecc | Elliptic Curve Cryptography tests |
| mac | Message Authentication Code tests |
| signature | Digital signature related tests |
| x25519 | X25519 elliptic curve key exchange tests |
| x448 | X448 elliptic curve key exchange tests |

### Post-Quantum Cryptography
| Tag | Description |
|-----|-------------|
| pq | Post-Quantum general tests |
| pq-sig | Post-Quantum signature tests |
| ml-dsa | Multi-Layer Digital Signature Algorithm tests |
| ml-kem | Multi-Layer Key Encapsulation Mechanism tests |
| hybrid-kem | Hybrid Key Encapsulation Mechanism tests |
| kem | Key Encapsulation Mechanism operations |


## Test Types
| Tag | Description |
|-----|-------------|
| smoke | Basic functionality tests |
| positive | Positive test scenarios |
| negative | Negative test cases |
| minimal | Minimal configuration tests |
| advanced | Advanced configuration tests |
| deprecated | Deprecated features tests |
| robot:skip-on-failure | Tests to skip on failure |


## Unsorted Tags
| Tag | Description |
|-----|-------------|
| batching | Batch processing tests |
| time | Timestamp-related tests |
| inconsistency | Inconsistent data handling tests |
| missing_info | Missing information handling tests |
| invalid-size | Message size validation tests |
| orig-pkimessage | Original PKI message handling tests |

## Transfer Mechanism Tags
| Tag | Description |
|-----|-------------|
| Transfer_HTTP |  |
| Transfer_CoAP |  |
| Transfer_File |  |
| Transfer_Offline |  |
| Transfer_Batched |  |
| Transfer_Nested |  |