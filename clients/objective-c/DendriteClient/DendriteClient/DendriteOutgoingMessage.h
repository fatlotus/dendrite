//
//  DendriteOutgoingMessage.h
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "DendriteClient.h"

@interface DendriteOutgoingMessage : NSObject

- (void)respondToReply:(DendriteMessageType*)type withSelector:(SEL)selector;

@end
