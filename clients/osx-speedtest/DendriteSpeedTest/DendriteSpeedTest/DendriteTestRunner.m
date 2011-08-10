//
//  DendriteTestRunner.m
//  DendriteSpeedTest
//
//  Created by Jeremy Archer on 8/10/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteTestRunner.h"

#pragma mark - Hidden Methods
@interface DendriteTestRunner (hidden)
- (void)write:(NSString *)string;
@end

@implementation DendriteTestRunner

#pragma mark - Speed Test Methods
- (void)startSpeedTest:(NSUInteger)number
{
    [self write:[NSString stringWithFormat:@"Running test with %i client(s).\n", number]];
    
    if (dendriteClientList)
        [self endSpeedTest];
    
    dendriteClientList = [[NSMutableArray arrayWithCapacity:number] retain];
    countClients = 0;
    
    numberOfClients = number;
    totalLatency = 0;
    
    switch(testingType) {
        case kTestTypeConcurrency:
            while (number-- > 0) {
                DendriteClient * client;
                client = [[DendriteClient alloc] initWithAddress:address
                                                            port:port
                                                     andDelegate:self];
                
                [client handleMessages:TypeIdentify withSelector:@selector(handleIdentify:)];
                
                [dendriteClientList addObject: client];
            }
            break;
        case kTestTypeLoad:
            [self addNextClient];
            break;
    }
}

- (void)addNextClient
{
    DendriteClient * client;
    client = [[DendriteClient alloc] initWithAddress:address
                                                port:port
                                         andDelegate:self];
    
    [client handleMessages:TypeIdentify withSelector:@selector(handleIdentify:)];
    
    [dendriteClientList addObject: client];
    
    if ([dendriteClientList count] < numberOfClients) {
        [self performSelector:@selector(addNextClient) withObject:nil afterDelay:0.1];
    }
}

- (void)endSpeedTest
{
    [self write: @"Speed test ended.\n"];
    [dendriteClientList release];
    dendriteClientList = nil;
}

#pragma mark - Response handler methods

- (void)handleIdentify:(DendriteIncomingMessage *)message
{
    NSString * userAgent, * deviceID;
    
    userAgent = [DendriteClient generateUserAgentString];
    deviceID = [DendriteClient generateDeviceIDString];
    
    [message replyWithType:TypeIdentity andArguments:userAgent, deviceID];
}

- (void)handleLoginSuccess:(DendriteIncomingMessage *)message
{
    [self endSpeedTest];
    
    [progressIndicator stopAnimation:self];
    [errorMessageLabel setStringValue:@""];
    
    runningFirstTest = NO;
    
    testingType = [testTypeButton selectedTag];
    
    [NSApp endSheet:infoSheet];
    
    [self startSpeedTest:[clientsField integerValue]];
}

- (void)handleLoginFailed:(DendriteIncomingMessage *)message
                  failure:(NSString *)failure
              description:(NSString *)description
{
    [self endSpeedTest];
    
    [progressIndicator stopAnimation:self];
    [errorMessageLabel setStringValue:@"Login failed."];
}

- (void)attemptToFinishLoginStage:(DendriteIncomingMessage *)message
{
    totalLatency += -[message.respondingToMessage.userInfo timeIntervalSinceNow];
    
    if (++countClients >= numberOfClients) {
        [self write:[NSString stringWithFormat:@"Average login latency: %.1fms\n", totalLatency * 1000 / numberOfClients]];
        
        countClients = 0;
        
        for (DendriteClient * client in dendriteClientList) {
            DendriteOutgoingMessage * outgoing;
            outgoing = [client sendMessage:TypeListen withArguments:@"local/", @""];
            [outgoing respondToReply:TypeSuccess withSelector:@selector(handleListenSuccess:)];
            [outgoing respondToReply:TypeNotify withSelector:@selector(handleListenNotify:type:data:)];
            [outgoing respondToReply:TypeFailure withSelector:@selector(handleListenFailure:failure:description:)];
            [outgoing setUserInfo:[NSDate date]];
        }
        
        totalLatency = 0;
    }
}

- (void)handleExpectedLoginSuccess:(DendriteIncomingMessage *)message
{
    [self attemptToFinishLoginStage:message];
}

- (void)handleUnexpectedLoginFailed:(DendriteIncomingMessage *)message failure:(NSString *)failure description:(NSString *)description
{
    [self write:[NSString stringWithFormat:@"Authentication failure: %@ (%@)\n", description, failure]];
    
    [self attemptToFinishLoginStage:message];
}

- (void)handleListenResponse:(DendriteIncomingMessage *)message
{
    totalLatency += -[message.respondingToMessage.userInfo timeIntervalSinceNow];
    
    if (++countClients >= numberOfClients) {
        [self write:[NSString stringWithFormat:@"Average listen latency: %.1fms\n", totalLatency * 1000 / numberOfClients]];
        
        countClients = 0;
        totalLatency = 0;
    }
}

- (void)handleListenSuccess:(DendriteIncomingMessage *)message
{
    [self handleListenResponse:message];
}

- (void)handleListenFailure:(DendriteIncomingMessage *)message failure:(NSString *)failure description:(NSString *)description
{
    [self write:[NSString stringWithFormat:@"Listen failure: %@ (%@)\n", description, failure]];
    
    [self handleListenResponse:message];
}

- (void)handleListenNotify:(DendriteIncomingMessage *)message type:(NSString *)type data:(NSDictionary *)dictionary
{
    
}

#pragma mark - Helpers
- (void)write:(NSString *)string
{
    [[outputView textStorage] appendAttributedString:[[[NSAttributedString alloc] initWithString:string] autorelease]];
}

#pragma mark - UI Helpers
- (BOOL)validateMenuItem:(NSMenuItem *)menuItem
{
    if (menuItem.tag == 0) {
        return (dendriteClientList != nil);
    } else {
        return (dendriteClientList == nil);
    }
}

#pragma mark - UI Actions
- (IBAction)cancelSpeedTest:(id)sender
{
    [self write:@"Cancelling speed test...\n"];
    [self endSpeedTest];
}

- (void)initializeUI
{
    [self write:@"Welcome to the Dendrite Speed Test!\nTo get started, navigate to Actions -> Start Concurrency Test above.\n"];
}

- (IBAction)runTest:(id)sender
{
    NSUInteger type = [sender tag];
    
    if (infoSheet == nil)
        [NSBundle loadNibNamed:@"OptionsSheet" owner:self];
    
    [testTypeButton selectItemWithTag:type];
    
    [NSApp beginSheet:infoSheet
       modalForWindow:mainWindow
        modalDelegate:self
       didEndSelector:@selector(didEndSheet:returnCode:contextInfo:)
          contextInfo:nil];
}

- (IBAction)testConnection:(id)sender
{
    runningFirstTest = YES;
    [progressIndicator startAnimation:self];
    address = [addressField stringValue];
    port = [portField integerValue];
    testingType = kTestTypeConcurrency;
    
    [errorMessageLabel setStringValue:@""];
    
    [self startSpeedTest:1];
}

- (void)connectedWithClient:(DendriteClient *)client
{
    DendriteOutgoingMessage * outgoingMessage;
    
    outgoingMessage = [client sendMessage:TypeLogin
                            withArguments:@"fatlotus", @"test"];
    
    [outgoingMessage setUserInfo:[NSDate date]];
    
    if (runningFirstTest) {
        [outgoingMessage respondToReply:TypeSuccess withSelector:@selector(handleLoginSuccess:)];
        [outgoingMessage respondToReply:TypeFailure withSelector:@selector(handleLoginFailed:failure:description:)];
    } else {
        [outgoingMessage respondToReply:TypeSuccess withSelector:@selector(handleExpectedLoginSuccess:)];
        [outgoingMessage respondToReply:TypeFailure withSelector:@selector(handleUnexpectedLoginFailed:failure:description:)];
    }
}

- (void)unconnectedWithClient:(DendriteClient *)client
{
    if (runningFirstTest) {
        [self endSpeedTest];
        
        [progressIndicator stopAnimation:self];
        [errorMessageLabel setStringValue:@"Connect failed."];
    } else {
        NSLog(@"Unconnected with client: %@", client);
    }
}

- (void)didEndSheet:(NSWindow *)sheet
         returnCode:(NSInteger)returnCode
        contextInfo:(void *)contextInfo
{
    [sheet orderOut:self];
}

@end
