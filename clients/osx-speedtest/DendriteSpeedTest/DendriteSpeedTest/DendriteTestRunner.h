//
//  DendriteTestRunner.h
//  DendriteSpeedTest
//
//  Created by Jeremy Archer on 8/10/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "DendriteClient.h"

#define kTestTypeConcurrency 1
#define kTestTypeLoad 2

@interface DendriteTestRunner : NSObject <DendriteClientDelegate> {
    IBOutlet NSWindow * mainWindow;
    IBOutlet NSWindow * infoSheet;
    IBOutlet NSTextView * outputView;
    IBOutlet NSProgressIndicator * progressIndicator;
    IBOutlet NSTextField * errorMessageLabel;
    
    IBOutlet NSTextField * addressField;
    IBOutlet NSTextField * portField;
    IBOutlet NSTextField * clientsField;
    IBOutlet NSPopUpButton * testTypeButton;
    
    NSMutableArray * dendriteClientList;
    NSString * address;
    NSUInteger port;
    BOOL runningFirstTest;
    NSUInteger numberOfClients;
    NSTimeInterval totalLatency;
    NSUInteger countClients;
    NSUInteger testingType;
}

#pragma mark - UI Actions
- (void)initializeUI;
- (IBAction)runTest:(id)sender;
- (IBAction)testConnection:(id)sender;
- (IBAction)cancelSpeedTest:(id)sender;

#pragma mark - Backend methods
- (void)startSpeedTest:(NSUInteger)number;
- (void)endSpeedTest;

@end
