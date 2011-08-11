//
//  DendriteClientTests.m
//  DendriteClientTests
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteClientTests.h"
#import "DendriteClient.h"
#import "SBJson.h"

#pragma mark - Test Implementation
@implementation DendriteClientTests

- (void)setUp
{
    [super setUp];
    
    testHelper = [[BlockingTestHelper alloc] init];
    client = [[DendriteClient alloc] initWithAddress:@"localhost" port:1337 andDelegate:self];
}

- (void)tearDown
{
    [client release];
    [testHelper release];
    
    [super tearDown];
}

#pragma mark - Test Methods
- (void)testExample
{
    [client handleMessages:TypeIdentify withSelector:@selector(handleIdentify:)];
    [client handleMessages:TypeEcho withSelector:@selector(handleEcho:)];
    
    [testHelper waitForEvent:@"connect"];
    [testHelper waitForEvent:@"login"];
}

#pragma mark - Protocol handling methods

- (void)handleEcho:(DendriteIncomingMessage *)msg {
    [msg replyWithType:TypeEcho andArguments:nil];
}

- (void)handleIdentify:(DendriteIncomingMessage *)msg {
    NSString * userAgent, * deviceIdentifier;
    
    userAgent = [DendriteClient generateUserAgentString];
    deviceIdentifier = [DendriteClient generateDeviceIDString];
    
    [msg replyWithType:TypeIdentity andArguments:userAgent, deviceIdentifier];
}

- (void)connectedWithClient:(DendriteClient *)_ {
    [testHelper triggerEvent:@"connect"];
    
    DendriteOutgoingMessage * message = [client sendMessage:TypeLogin withArguments:@"fred", @"fredspassword"];
    [message respondToReply:TypeSuccess withSelector:@selector(loginSuccessful:)];
    [message respondToReply:TypeFailure withSelector:@selector(loginFailed:failure:description:)];
}

- (void)handleSessionData:(DendriteClient *)_ data:(NSDictionary *)data {
    [testHelper triggerEvent:@"login"];
    
    NSLog(@"Login successful.", data);
}

- (void)loginSuccessful:(DendriteIncomingMessage *)message {
    DendriteOutgoingMessage * outgoing = [client sendMessage:TypeSession withArguments:nil];
    [outgoing respondToReply:TypeData withSelector:@selector(handleSessionData:data:)];
}

- (void)loginFailed:(DendriteIncomingMessage*)_ failure:(NSString*)failure description:(NSString*)description {
    [testHelper triggerEvent:@"login"];
    
    NSLog(@"Login failed: %@", description);
}

- (void)unconnectedWithClient:(DendriteClient *)client {
    NSLog(@"Unable to connect to server.");
}

@end
