//
//  DendriteClient.m
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteClient.h"
#import "AsyncSocket.h"

#pragma mark Array Initializers (hidden)

DendriteMessageType dendriteMessageTypeTable[] = {
    /*0x00*/ _none,
    /*0x01*/ TypeEcho,
    /*0x02*/ TypeFetch,
    /*0x03*/ TypeListen,
    /*0x04*/ TypeNotify,
    /*0x05*/ TypeCancel,
    /*0x06*/ _none,
    /*0x07*/ _none,
    /*0x08*/ TypeData,
    /*0x09*/ TypeLogin,
    /*0x0A*/ TypeSuccess,
    /*0x0B*/ TypeFailure,
    /*0x0C*/ TypeIdentity,
    /*0x0D*/ TypeIdentify
};

/*
 * The type codes are as follows:
 * 
 * s UTF8 String
 * d JSON-encoded data
 * u Unsigned 32-bit integer
 * i Signed 32-bit integer
 * b Boolean value (1 for YES, 0 for NO)
 *
 */
char * dendriteMessageArgumentTypesTable[] = {
    /*0x00*/ "!",
    /*0x01*/ "",
    /*0x02*/ "ss",
    /*0x03*/ "ss",
    /*0x04*/ "sd",
    /*0x05*/ "",
    /*0x06*/ "!",
    /*0x07*/ "!",
    /*0x08*/ "d",
    /*0x09*/ "ss",
    /*0x0A*/ "",
    /*0x0B*/ "ss",
    /*0x0C*/ "ss",
    /*0x0D*/ ""
};

#pragma mark - Tag Identifiers

#define kTagWaitingForLength 1
#define kTagWaitingForFields 2

#pragma mark - Private interfaces for incoming and outgoing messages

@interface DendriteOutgoingMessage (hidden)

- (id)initWithDendriteClient:(DendriteClient *)client;
- (NSInvocation*)invocationForTypeID:(NSUInteger)typeID;

@end

@interface DendriteIncomingMessage (hidden)

- (id)initWithClient:(DendriteClient *)client andMessageID:(NSUInteger)messageID;

@end

#pragma mark - Private helper methods

@interface DendriteClient (hidden)

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                             withReplyTo:(NSUInteger)replyTo
                            andArguments:(NSArray*)arguments;
- (void)rememberForRepliesFrom:(DendriteOutgoingMessage *)outgoingMessage;

@end

#pragma mark - DendriteClient Implementation

@implementation DendriteClient

@synthesize delegate;

#pragma mark Table conversion methods

+ (DendriteMessageType)typeFromTypeID:(NSUInteger)typeID
{
    return dendriteMessageTypeTable[typeID];
}

+ (NSUInteger)typeIDFromType:(DendriteMessageType)type
{
    for (NSUInteger i = 0; i < kDendriteHighestTypeIDPlusOne; i++) {
        if (dendriteMessageTypeTable[i] == type) {
            return i;
        }
    }
    
    [NSException raise:@"UndefinedType" format:@"Unknown message type."];
    return 0;
}

#pragma mark - Constructors

- (id)initWithAddress:(NSString*)host port:(NSUInteger)port andDelegate:(id<DendriteClientDelegate>)defaultDelegate
{
    self = [super init];
    
    if (self != nil) {
        for (NSUInteger i = 0; i < kDendriteHighestTypeIDPlusOne; i++) {
            defaultResponses[i] = nil;
        }
        
        messageResponseHandlers = [[NSMutableDictionary alloc] initWithCapacity:10];
        
        delegate = defaultDelegate;
        
        incomingMessageNonce = 0;
        outgoingMessageNonce = 1;
        
        socket = [[AsyncSocket alloc] initWithDelegate:self];
        [socket connectToHost:host onPort:(uint16_t)port withTimeout:kDendriteClientDefaultTimeout error:nil];
        
        NSMutableDictionary * tlsOptions = [NSMutableDictionary dictionaryWithCapacity:1];
        [tlsOptions setObject:kCFBooleanFalse forKey:kCFStreamSSLValidatesCertificateChain];
        [tlsOptions setObject:kCFBooleanTrue forKey:kCFStreamSSLAllowsAnyRoot];
        [socket startTLS:tlsOptions];
        
        [socket readDataToLength:9 withTimeout:(NSTimeInterval)(-1.0) tag:kTagWaitingForLength];
    }
    
    return self;
}

#pragma mark - Public Interface

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                           withArguments:(id)argument, ...
{
    va_list args;
    va_start(args, argument);
    
    NSMutableArray * argumentsAsArray = [NSMutableArray arrayWithCapacity:10]; 
    
    NSUInteger numberOfArguments = strlen(dendriteMessageArgumentTypesTable[[DendriteClient typeIDFromType:type]]);
    
    if (numberOfArguments >= 1)
        [argumentsAsArray addObject:argument];
    
    for (NSUInteger i = 1, l = numberOfArguments; i < l; i++) {
        [argumentsAsArray addObject: va_arg(args, id)];
    }
    
    va_end(args);
    
    return [self sendMessage:type withReplyTo:outgoingMessageNonce andArguments:argumentsAsArray];
}

- (void)handleMessages:(DendriteMessageType)type
          withSelector:(SEL)selector
{
    NSUInteger typeID = [DendriteClient typeIDFromType:type];
    
    if (defaultResponses[typeID] != nil) {
        [NSException raise:@"InvalidInvocation" format:@""];
    }
    
    NSInvocation * invocation = [NSInvocation invocationWithMethodSignature:[delegate methodSignatureForSelector:selector]];
    [invocation setSelector:selector];
    [invocation retain];
    
    defaultResponses[typeID] = invocation;
}

#pragma mark - Encoding helper methods

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                             withReplyTo:(NSUInteger)replyTo
                            andArguments:(NSArray*)arguments
{
    DendriteOutgoingMessage * msg = [[[DendriteOutgoingMessage alloc] initWithDendriteClient:self] autorelease];
    [messageResponseHandlers setObject:msg forKey:[NSNumber numberWithUnsignedLong:outgoingMessageNonce]];
    
    uint8_t typeID = [DendriteClient typeIDFromType:type];
    
    NSMutableData * fields = [NSMutableData dataWithCapacity:50];
    char * types = dendriteMessageArgumentTypesTable[typeID];
    
    if (strlen(types) != [arguments count]) {
        [NSException raise:@"ArgumentCountMismatch" format:@"Message type %@ requires %i arguments, but you only passed %i", typeID, strlen(types), [arguments count]];
        return nil;
    }
    
    for (NSUInteger i = 0; i < [arguments count]; i++) {
        char type = types[i];
        id object = [arguments objectAtIndex:i];
        
        if (type == 's' && [object isKindOfClass:[NSString class]]) {
            NSData * encodedAsUTF8 = [(NSString*)object dataUsingEncoding:NSUTF8StringEncoding];
            uint16_t length = htons((uint16_t)[encodedAsUTF8 length]);
            
            [fields appendBytes:&length length:sizeof(uint16_t)];
            [fields appendData:encodedAsUTF8];
        } else if (type == 'd') {
            NSData * encodedAsUTF8 = [[object JSONRepresentation] dataUsingEncoding:NSUTF8StringEncoding];
            uint16_t length = htons((uint16_t)[encodedAsUTF8 length]);
            
            [fields appendBytes:&length length:sizeof(uint16_t)];
            [fields appendData:encodedAsUTF8];
        } else if (type == 'u' && [object isKindOfClass:[NSNumber class]]) {
            uint32_t data = htonl([object unsignedIntValue]);
            [fields appendBytes:&data length:sizeof(uint32_t)]; 
        } else if (type == 'i' && [object isKindOfClass:[NSNumber class]]) {
            int32_t data = htonl([object intValue]);
            [fields appendBytes:&data length:sizeof(int32_t)];
        } else {
            [NSException raise:@"Invalid argument." format:@"Expecting an object coercable to %c, but got a %@", type, [object class]];
        }
    }
    
    NSMutableData * buffer;
    
    buffer = [NSMutableData dataWithCapacity:50];
    
    uint32_t encodedReply = htonl(replyTo);
    uint32_t encodedLength = htonl([fields length]);
    
    [buffer appendBytes:&encodedReply length:sizeof(uint32_t)];
    [buffer appendBytes:&typeID length:sizeof(uint8_t)];
    [buffer appendBytes:&encodedLength length:sizeof(uint32_t)];
    [buffer appendData:fields];
    
    [socket writeData:buffer withTimeout:(NSTimeInterval)(-1) tag:0];
    
    outgoingMessageNonce += 2;
    
    return msg;
}

#pragma mark - AsyncSocket delegate methods

- (void)onSocketDidSecure:(AsyncSocket *)sock
{
    if (delegate != nil && [delegate respondsToSelector:@selector(connectedWithClient:)])
        [delegate connectedWithClient:self];
}

- (void)onSocket:(AsyncSocket *)sock didReadData:(NSData *)data withTag:(long)tag
{
    if (tag == kTagWaitingForLength) {
        uint32_t packedMessageReplyTo;
        uint32_t packedMessageLength;
        
        [data getBytes:&packedMessageReplyTo range:NSMakeRange(0, 4)];
        [data getBytes:&incomingMessageTypeID range:NSMakeRange(4, 1)];
        [data getBytes:&packedMessageLength range:NSMakeRange(5, 4)];
        
        incomingMessageReplyTo = ntohl(packedMessageReplyTo);
        
        uint32_t messageLength = ntohl(packedMessageLength);
        
        if (messageLength > 0) {
            [socket readDataToLength:messageLength withTimeout:(NSTimeInterval)(-1) tag:kTagWaitingForFields];
        } else {
            [self onSocket:sock didReadData:[NSData data] withTag:kTagWaitingForFields];
        }
        
    } else if (tag == kTagWaitingForFields) {
        
        NSInvocation * response;
        
        DendriteIncomingMessage * incomingMessage = [[[DendriteIncomingMessage alloc] initWithClient:self andMessageID:incomingMessageNonce] autorelease];
        
        if (incomingMessageReplyTo != incomingMessageNonce) {
            
            DendriteOutgoingMessage * message = [messageResponseHandlers objectForKey:[NSNumber numberWithUnsignedLong:incomingMessageReplyTo]];
            
            if (message == nil) {
                [NSException raise:@"UnknownResponse" format:@"Got message in reply to unknown message."];
            }
            
            response = [message invocationForTypeID:incomingMessageTypeID];
            
        } else {
            
            response = defaultResponses[incomingMessageTypeID]; 
            
        }
        
        if (response == nil) {
            [NSException raise:@"InvalidResponse" format:@"Registerred no response to request of type %d", incomingMessageTypeID];
        }
        
        char * fieldTypes = dendriteMessageArgumentTypesTable[incomingMessageTypeID];
        NSUInteger o/*ffset*/;
        NSString * stringRead;
        id result;
        BOOL boolResult;
        uint32_t int32;
        uint8_t int8;
        
        o = 0;
        
        [response setArgument:&incomingMessage atIndex:2];
        
        for (NSUInteger i = 0, l = strlen(fieldTypes); i < l; i++) {
            switch (fieldTypes[i]) {
                case 's':
                case 'd':
                    
                    [data getBytes:&int32 range:NSMakeRange(o,4)];
                    int32 = ntohl(int32);
                    NSLog(@"int32: %i", int32);
                    
                    o += 4;
                    stringRead = [[NSString alloc] initWithData:[data subdataWithRange:NSMakeRange(o, int32)] encoding:NSUTF8StringEncoding];
                    o += int32;
                    
                    if (fieldTypes[i] == 'd') {
                        result = [stringRead JSONValue];
                    } else {
                        result = stringRead;
                    }
                    [response setArgument:&stringRead atIndex:(i+3)];
                    
                    break;
                
                case 'u':
                case 'i':
                    
                    [data getBytes:&int32 range:NSMakeRange(o, 4)];
                    o += 4;
                    int32 = ntohl(int32);
                    
                    [response setArgument:&int32 atIndex:(i+3)];
                    
                    break;
                
                case 'b':
                    
                    [data getBytes:&int8 range:NSMakeRange(o, 1)];
                    o += 1;
                    boolResult = (int8 == 1);
                    [response setArgument:&boolResult atIndex:(i+3)];
                    
                    break;
                
                default:
                    
                    [NSException raise:@"Invalid" format:@"Unknown field type qualifier \"%c\" for opcode %i.", fieldTypes[i], incomingMessageTypeID];
                    break;
            }
        }
        
        incomingMessageNonce += 2;
        
        [socket readDataToLength:9 withTimeout:(NSTimeInterval)(-1.0) tag:kTagWaitingForLength];
        
        [response setTarget:delegate];
        [response invoke];
    }
}

- (void)dealloc {
    for (NSUInteger i = 0; i < kDendriteHighestTypeIDPlusOne; i++) {
        [defaultResponses[i] release];
    }
    
    [messageResponseHandlers release];
    [socket disconnect];
    [socket release];
    [super dealloc];
}

@end