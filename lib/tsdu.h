#pragma once

#define D_REJECT			0x08
#define D_REFUSAL			0x09
#define U_END				0x0a
#define D_BACK_CCH			0x0b
#define D_RELEASE			0x0c
#define U_ABORT				0x0d
#define U_TERMINATE			0x0e
#define D_HOOK_ON_INVITATION		0x0f
#define D_RETURN			0x10
#define U_EVENT_REPORT			0x11
#define D_CALL_WAITING			0x12
#define D_AUTHENTICATION		0x13
#define U_AUTHENTICATION		0x14
#define D_AUTHORISATION			0x16
#define U_ERROR_REPORT			0x17
#define D_CHANNEL_INIT			0x18
#define U_REGISTRATION_REQ		0x20
#define D_REGISTRATION_NAK		0x21
#define D_REGISTRATION_ACK		0x22
#define D_FORCED_REGISTRATION		0x23
#define U_LOCATION_ACTIVITY		0x24
#define D_LOCATION_ACTIVITY_ACK		0x25
#define U_CALL_SETUP			0x30
#define D_CALL_ALERT			0x31
#define D_CALL_SETUP			0x32
#define U_CALL_ANSWER			0x33
#define D_CALL_CONNECT			0x34
#define D_CALL_SWITCH			0x35
#define U_CALL_INTRUSION_PC		0x36
#define U_CALL_INTRUSION_OCH		0x37
#define D_TRANSFER_NAK			0x39
#define U_TRANSFER_REQ			0x3a
#define U_CALL_INTRUSION_ECH		0x3b
#define U_CALL_RELEASE			0x3c
#define U_CALL_CONNECT			0x3d
#define U_CALL_SWITCH			0x3d
#define D_CALL_START			0x3e
#define D_CALL_ACTIVATION		0xe0
#define D_CALL_COMPOSITION		0xe1
#define D_CALL_END			0xe2
#define D_CALL_OVERLOAD_ID		0xe3
#define D_FUNCTIONAL_SHORT_DATA		0x42
#define U_DATA_DOWN_ACCEPT		0x43
#define U_DATA_MSG_UP			0x44
#define D_DATA_MSG_DOWN			0x45
#define D_EXPLICIT_SHORT_DATA		0x46
#define D_DATA_END			0x48
#define D_DATAGRAM_NOTIFY		0x49
#define D_DATAGRAM			0x4a
#define D_BROADCAST			0x4b
#define D_DATA_SERV			0x4c
#define D_DATA_DOWN_STATUS		0x4e
#define D_CONNECT_DCH			0x60
#define D_CONNECT_CCH			0x62
#define D_DATA_AUTHENTICATION		0x63
#define D_DATA_REQUEST			0x64
#define D_DCH_OPEN			0x65
#define U_DATA_REQUEST			0x66
#define D_EXTENDED_STATUS		0x67
#define D_CCH_OPEN			0x68
#define D_BROADCAST_WAITING		0x69
#define U_OCH_RELEASE			0x50
#define U_OCH_SETUP			0x51
#define U_ECH_CLOSE			0x52
#define D_EMERGENCY_NOTIFICATION	0x53
#define U_ECH_SETUP			0x54
#define D_GROUP_ACTIVATION		0x55
#define D_ECH_ACTIVATION		0x56
#define D_GROUP_END			0x57
#define D_GROUP_IDLE			0x58
#define D_GROUP_REJECT			0x59
#define D_ECH_REJECT			0x5a
#define D_GROUP_PAGING			0x5b
#define D_BROADCAST_NOTIFICATION	0x5c
#define D_CRISIS_NOTIFICATION		0x5d
#define D_EMERGENCY_ACK			0x5f
#define D_EMERGENCY_NAK			0x80
#define U_EMERGENCY_REQ			0x81
#define D_GROUP_OVERLOAD_ID		0x82
#define D_ECH_OVERLOAD_ID		0x83
#define D_PRIORITY_GRP_WAITING		0x84
#define D_PRIORITY_GRP_ACTIVATION	0x85
#define D_OC_ACTIVATION			0x86
#define D_OC_REJECT			0x87
#define D_OC_PAGING			0x88
#define D_ACCESS_DISABLED		0x70
#define D_TRAFFIC_ENABLED		0x71
#define D_TRAFFIC_DISABLED		0x72
#define U_DEVIATION_CLEAR		0x73
#define U_DEVIATION_SET			0x74
#define D_DEVIATION_ON			0x76
#define D_SERVICE_DISABLED		0x78
#define D_ABILITY_MNGT			0x77
#define D_SYSTEM_INFO			0x90
#define D_GROUP_LIST			0x92
#define D_GROUP_COMPOSITION		0x93
#define D_NEIGHBOURING_CELL		0x94
#define D_ECCH_DESCRIPTION		0x95
#define D_ADDITIONAL_PARTICIPANTS	0x96
#define D_INFORMATION_DELIVERY		0xc5


#define IEI_GROUP_ID			0x01
#define IEI_CELL_ID_LIST		0x02
#define IEI_KEY_OF_CALL			0x03
#define IEI_ADJACENT_BN_LIST		0x04
#define IEI_TTI				0x05
#define IEI_ADR				0x06
#define IEI_USER_PRIORITY		0x81
#define IEI_COVERAGE_ID			0x82
#define IEI_KEY_REFERENCE		0x83
#define IEI_ADD_SETUP_PARAM		0x84
#define IEI_PROFILE_ID			0x85

void tsdu_process(const uint8_t* t, int data_length, int mod);

void decode_bch(const uint8_t *t);
void decode_pch(const uint8_t *t);
void decode_rch(const uint8_t *t);
// TODO
void decode_rch_addressconst (uint8_t *t);
